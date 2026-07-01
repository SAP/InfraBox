"""
MCP builds endpoints.
GET  /api/v1/mcp/projects/<project_id>/builds
GET  /api/v1/mcp/projects/<project_id>/builds/<build_id>
POST /api/v1/mcp/projects/<project_id>/trigger
"""
import uuid as _uuid

from flask import g, abort
from flask_restx import Resource

from pyinfraboxutils.ibrestplus import api
from api.handlers.mcp.auth import mcp_auth_required, check_project_access_mcp, check_trigger_access_mcp
from api.handlers.mcp.rate_limit import mcp_rate_limit
from api.handlers.mcp.audit import audit_mcp

ns = api.namespace('MCP Builds',
                   path='/api/v1/mcp/projects/<project_id>',
                   description='MCP build operations')


@ns.route('/builds')
class MCPBuilds(Resource):
    @mcp_auth_required
    @mcp_rate_limit('list_builds')
    def get(self, project_id):
        """List builds for a project."""
        audit_mcp('list_builds', outcome='attempt', details={'project_id': project_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('list_builds', outcome='forbidden', details={'project_id': project_id})
            abort(403, 'access to this project is not permitted for the current MCP token')

        try:
            rows = g.db.execute_many_dict('''
                SELECT b.id, b.build_number, b.restart_counter, b.project_id, b.commit_id,
                       c.branch,
                       MIN(j.created_at)                                        AS created_at,
                       MAX(j.end_date)                                          AS finished_at,
                       CASE
                           WHEN bool_or(j.state IN ('running','queued','scheduled')) THEN 'running'
                           WHEN bool_or(j.state = 'failure')  THEN 'failure'
                           WHEN bool_or(j.state = 'error')    THEN 'error'
                           WHEN bool_or(j.state = 'killed')   THEN 'killed'
                           WHEN bool_or(j.state = 'unstable') THEN 'unstable'
                           WHEN bool_and(j.state = 'finished') THEN 'finished'
                           ELSE NULL
                       END                                                      AS status
                FROM build b
                LEFT JOIN commit c ON c.id = b.commit_id
                LEFT JOIN job j    ON j.build_id = b.id
                WHERE b.project_id = %s
                GROUP BY b.id, b.build_number, b.restart_counter, b.project_id, b.commit_id, c.branch
                ORDER BY b.build_number DESC, b.restart_counter DESC
                LIMIT 50
            ''', [project_id])
            result = [_build_dict(r) for r in rows]
            audit_mcp('list_builds', outcome='success',
                      details={'project_id': project_id, 'count': len(result)})
            return result
        except Exception as exc:
            audit_mcp('list_builds', outcome='failure',
                      details={'project_id': project_id}, error=str(exc))
            raise


@ns.route('/builds/<build_id>')
class MCPBuild(Resource):
    @mcp_auth_required
    @mcp_rate_limit('list_builds')
    def get(self, project_id, build_id):
        """Get a single build by ID."""
        audit_mcp('get_build', outcome='attempt',
                  details={'project_id': project_id, 'build_id': build_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('get_build', outcome='forbidden', details={'project_id': project_id})
            abort(403, 'access to this project is not permitted for the current MCP token')

        try:
            rows = g.db.execute_many_dict('''
                SELECT b.id, b.build_number, b.restart_counter, b.project_id, b.commit_id,
                       c.branch,
                       MIN(j.created_at)                                        AS created_at,
                       MAX(j.end_date)                                          AS finished_at,
                       CASE
                           WHEN bool_or(j.state IN ('running','queued','scheduled')) THEN 'running'
                           WHEN bool_or(j.state = 'failure')  THEN 'failure'
                           WHEN bool_or(j.state = 'error')    THEN 'error'
                           WHEN bool_or(j.state = 'killed')   THEN 'killed'
                           WHEN bool_or(j.state = 'unstable') THEN 'unstable'
                           WHEN bool_and(j.state = 'finished') THEN 'finished'
                           ELSE NULL
                       END                                                      AS status
                FROM build b
                LEFT JOIN commit c ON c.id = b.commit_id
                LEFT JOIN job j    ON j.build_id = b.id
                WHERE b.id = %s AND b.project_id = %s
                GROUP BY b.id, b.build_number, b.restart_counter, b.project_id, b.commit_id, c.branch
            ''', [build_id, project_id])
            if not rows:
                abort(404)
            result = _build_dict(rows[0])
            audit_mcp('get_build', outcome='success',
                      details={'project_id': project_id, 'build_id': build_id})
            return result
        except Exception as exc:
            audit_mcp('get_build', outcome='failure',
                      details={'project_id': project_id, 'build_id': build_id}, error=str(exc))
            raise


@ns.route('/trigger')
class MCPTrigger(Resource):
    @mcp_auth_required
    @mcp_rate_limit('trigger_build')
    def post(self, project_id):
        """Trigger a new build (requires allow_trigger on the MCP token)."""
        if not check_project_access_mcp(project_id):
            audit_mcp('trigger_build', outcome='forbidden', details={'project_id': project_id})
            abort(403, 'access to this project is not permitted for the current MCP token')

        if not check_trigger_access_mcp():
            audit_mcp('trigger_build', outcome='forbidden',
                      details={'project_id': project_id, 'reason': 'trigger not allowed'})
            abort(403, 'this MCP token does not have trigger permission')

        project = g.db.execute_one_dict('''
            SELECT id, type FROM project WHERE id = %s
        ''', [project_id])
        if not project:
            abort(404)
        if project['type'] not in ('upload', 'test'):
            return {
                'message': 'trigger is only supported for upload/test type projects via MCP',
                'status': 400,
            }, 400

        try:
            build_id = str(_uuid.uuid4())
            g.db.execute('LOCK TABLE build IN EXCLUSIVE MODE')
            g.db.execute('''
                INSERT INTO build (id, project_id, build_number, restart_counter, source)
                SELECT %s, %s, COALESCE(MAX(build_number), 0) + 1, 0, 'mcp'
                FROM build WHERE project_id = %s
            ''', [build_id, project_id, project_id])
            g.db.commit()
            audit_mcp('trigger_build', outcome='success',
                      details={'project_id': project_id, 'build_id': build_id})
            return {'build_id': build_id, 'status': 200}, 200
        except Exception as exc:
            audit_mcp('trigger_build', outcome='failure',
                      details={'project_id': project_id}, error=str(exc))
            raise


def _build_dict(r):
    return {
        'id': r['id'],
        'build_number': r['build_number'],
        'restart_counter': r['restart_counter'],
        'project_id': r['project_id'],
        'commit_id': r.get('commit_id'),
        'branch': r.get('branch'),
        'created_at': r['created_at'].isoformat() if r.get('created_at') else None,
        'finished_at': r['finished_at'].isoformat() if r.get('finished_at') else None,
        'status': r.get('status'),
    }
