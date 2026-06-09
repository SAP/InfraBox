"""
MCP builds endpoints.
GET  /api/v1/mcp/projects/<project_id>/builds
POST /api/v1/mcp/projects/<project_id>/trigger
"""
import uuid as _uuid

from flask import g, jsonify, abort
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
                SELECT id, build_number, restart_counter, project_id, commit_id,
                       branch, created_at, finished_at, status
                FROM build
                WHERE project_id = %s
                ORDER BY build_number DESC, restart_counter DESC
                LIMIT 50
            ''', [project_id])
            result = [_build_dict(r) for r in rows]
            audit_mcp('list_builds', outcome='success',
                      details={'project_id': project_id, 'count': len(result)})
            return jsonify(result)
        except Exception as exc:
            audit_mcp('list_builds', outcome='failure',
                      details={'project_id': project_id}, error=str(exc))
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

        # Delegate to the existing /api/v1/projects/<id>/trigger endpoint internals.
        # We do this by calling the DB-level trigger path that creates a build entry
        # for manual (upload-type) triggers.  Full GitHub/gerrit triggers are handled
        # by the existing endpoint and are out of scope for MCP.
        project = g.db.execute_one_dict('''
            SELECT id, type FROM project WHERE id = %s
        ''', [project_id])
        if not project:
            abort(404)
        if project['type'] not in ('upload', 'test'):
            return jsonify({
                'message': 'trigger is only supported for upload/test type projects via MCP',
                'status': 400,
            }), 400

        try:
            build_id = str(_uuid.uuid4())
            # Lock the table so concurrent triggers compute non-duplicate build numbers,
            # matching the pattern used by the existing trigger endpoint (trigger.py).
            g.db.execute('LOCK TABLE build IN EXCLUSIVE MODE')
            g.db.execute('''
                INSERT INTO build (id, project_id, build_number, restart_counter, source)
                SELECT %s, %s, COALESCE(MAX(build_number), 0) + 1, 0, 'mcp'
                FROM build WHERE project_id = %s
            ''', [build_id, project_id, project_id])
            g.db.commit()
            audit_mcp('trigger_build', outcome='success',
                      details={'project_id': project_id, 'build_id': build_id})
            return jsonify({'build_id': build_id, 'status': 200}), 200
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
