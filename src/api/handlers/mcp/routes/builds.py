"""
MCP builds endpoints.
GET    /api/v1/mcp/projects/<project_id>/builds
GET    /api/v1/mcp/projects/<project_id>/builds/<build_id>
POST   /api/v1/mcp/projects/<project_id>/trigger
POST   /api/v1/mcp/projects/<project_id>/builds/<build_id>/restart
DELETE /api/v1/mcp/projects/<project_id>/builds/<build_id>/abort
"""
import json
import uuid as _uuid

from flask import g, abort
from flask_restx import Resource

from pyinfraboxutils.ibrestplus import api
from api.handlers.mcp.auth import (
    mcp_auth_required,
    check_project_access_mcp,
    check_trigger_access_mcp,
    get_mcp_user_id,
)
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
            job_id = str(_uuid.uuid4())

            # Resolve source_upload_id based on project type.
            # - upload: reuse the most recent source_upload for this project
            # - test:   source_upload_id may be NULL (schema allows it)
            source_upload_id = None
            if project['type'] == 'upload':
                src = g.db.execute_one_dict('''
                    SELECT id FROM source_upload
                    WHERE project_id = %s ORDER BY id DESC LIMIT 1
                ''', [project_id])
                if not src:
                    audit_mcp('trigger_build', outcome='failure',
                              details={'project_id': project_id,
                                       'reason': 'no source_upload for upload-type project'})
                    return {
                        'message': 'no source_upload; upload code before triggering',
                        'status': 409,
                    }, 409
                source_upload_id = src['id']

            g.db.execute('LOCK TABLE build IN EXCLUSIVE MODE')

            # 1) INSERT build row — restart_counter defaults to schema default (1) to stay
            #    compatible with legacy queries (project.py:85 etc.) that filter on rc = 1.
            g.db.execute('''
                INSERT INTO build (id, project_id, build_number, source, source_upload_id)
                SELECT %s, %s, COALESCE(MAX(build_number), 0) + 1, 'mcp', %s
                FROM build WHERE project_id = %s
            ''', [build_id, project_id, source_upload_id, project_id])

            # 2) INSERT the seed "Create Jobs" job — this is the ONLY path that lets the
            #    scheduler pick up the build (scheduler polls the job table, not the build table).
            definition = {
                'build_only': False,
                'resources': {'limits': {'cpu': 0.5, 'memory': 1024}},
            }
            g.db.execute('''
                INSERT INTO job (id, state, build_id, type, name, project_id,
                                 dockerfile, definition, cluster_name)
                VALUES (%s, 'queued', %s, 'create_job_matrix',
                        'Create Jobs', %s, '', %s, NULL)
            ''', [job_id, build_id, project_id, json.dumps(definition)])

            g.db.commit()
            # Audit success only after the seed job is committed — a build without a seed job
            # is a zombie and must not be recorded as success.
            audit_mcp('trigger_build', outcome='success',
                      details={'project_id': project_id, 'build_id': build_id,
                               'source_upload_id': source_upload_id})
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


@ns.route('/builds/<build_id>/restart')
class MCPBuildRestart(Resource):
    @mcp_auth_required
    @mcp_rate_limit('trigger_build')  # share the trigger bucket for all write ops
    def post(self, project_id, build_id):
        """Restart a build: creates a new build entry with incremented restart_counter
        and re-clones the Create Jobs seed job. Requires allow_trigger on the MCP token."""
        audit_mcp('restart_build', outcome='attempt',
                  details={'project_id': project_id, 'build_id': build_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('restart_build', outcome='forbidden', details={'project_id': project_id})
            abort(403, 'access to this project is not permitted for the current MCP token')

        if not check_trigger_access_mcp():
            audit_mcp('restart_build', outcome='forbidden',
                      details={'project_id': project_id,
                               'build_id': build_id, 'reason': 'trigger not allowed'})
            abort(403, 'this MCP token does not have trigger permission')

        # Fetch the original build. check_project_access_mcp has already gated access.
        build = g.db.execute_one_dict('''
            SELECT *
            FROM build
            WHERE id = %s AND project_id = %s
        ''', [build_id, project_id])
        if not build:
            audit_mcp('restart_build', outcome='failure',
                      details={'project_id': project_id, 'build_id': build_id,
                               'reason': 'build not found'})
            abort(404)

        try:
            # Lock the build table BEFORE reading max(restart_counter) so two
            # concurrent restarts of the same build_number cannot both read the
            # same max and insert duplicate restart_counter rows. The lock is held
            # until the commit at the end of this try block. Do NOT call audit_mcp()
            # between here and the commit — audit uses its own connection now, but
            # keeping the locked section audit-free avoids any future regression.
            g.db.execute('LOCK TABLE build IN EXCLUSIVE MODE')

            # Compute next restart_counter for this build_number.
            # MAX() returns NULL (-> None) if no rows match; guard with `or 0`
            # so we never do None + 1. (COALESCE in SQL would work too, matching
            # the pattern MCPTrigger uses for build_number.)
            row = g.db.execute_one_dict('''
                SELECT max(restart_counter) AS restart_counter
                FROM build
                WHERE build_number = %s AND project_id = %s
            ''', [build['build_number'], project_id])
            restart_counter = (row['restart_counter'] or 0) + 1

            # Insert the new build row referencing the same commit/source_upload.
            new_build_row = g.db.execute_one_dict('''
                INSERT INTO build (commit_id, build_number, project_id,
                                   restart_counter, source_upload_id)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            ''', [build['commit_id'],
                  build['build_number'],
                  project_id,
                  restart_counter,
                  build['source_upload_id']])
            new_build_id = new_build_row['id']

            # Clone the original Create Jobs seed job so the scheduler picks up the new build.
            seed = g.db.execute_one_dict('''
                SELECT repo, env_var, definition
                FROM job
                WHERE project_id = %s
                  AND name = 'Create Jobs'
                  AND build_id = %s
            ''', [project_id, build_id])
            if not seed:
                # Roll back the just-inserted build so we don't leave an orphan
                # build row (and release the LOCK) before auditing/aborting.
                g.db.rollback()
                audit_mcp('restart_build', outcome='failure',
                          details={'project_id': project_id, 'build_id': build_id,
                                   'reason': 'original build has no Create Jobs seed'})
                abort(500, 'original build is missing the Create Jobs seed job')

            env_var = json.dumps(seed['env_var']) if seed['env_var'] else None
            repo = json.dumps(seed['repo']) if seed['repo'] else None
            definition = json.dumps(seed['definition']) if seed['definition'] else None

            job_id = str(_uuid.uuid4())
            msg = 'Build restarted by MCP token (user %s)\n' % get_mcp_user_id()
            g.db.execute('''
                INSERT INTO job (id, state, build_id, type,
                    name, project_id, dockerfile, repo, env_var, definition, cluster_name)
                VALUES (%s, 'queued', %s, 'create_job_matrix',
                        'Create Jobs', %s, '', %s, %s, %s, NULL);
                INSERT INTO console (job_id, output)
                VALUES (%s, %s);
            ''', [job_id, new_build_id, project_id, repo, env_var, definition, job_id, msg])
            g.db.commit()

            audit_mcp('restart_build', outcome='success',
                      details={'project_id': project_id, 'build_id': build_id,
                               'new_build_id': new_build_id,
                               'restart_counter': restart_counter})
            return {
                'build_id': new_build_id,
                'restart_counter': restart_counter,
                'status': 200,
            }, 200
        except Exception as exc:
            audit_mcp('restart_build', outcome='failure',
                      details={'project_id': project_id, 'build_id': build_id},
                      error=str(exc))
            raise


@ns.route('/builds/<build_id>/abort')
class MCPBuildAbort(Resource):
    @mcp_auth_required
    @mcp_rate_limit('trigger_build')  # share the trigger bucket
    def delete(self, project_id, build_id):
        """Abort every running/queued job in a build. Requires allow_trigger on the MCP token."""
        audit_mcp('abort_build', outcome='attempt',
                  details={'project_id': project_id, 'build_id': build_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('abort_build', outcome='forbidden', details={'project_id': project_id})
            abort(403, 'access to this project is not permitted for the current MCP token')

        if not check_trigger_access_mcp():
            audit_mcp('abort_build', outcome='forbidden',
                      details={'project_id': project_id,
                               'build_id': build_id, 'reason': 'trigger not allowed'})
            abort(403, 'this MCP token does not have trigger permission')

        try:
            jobs = g.db.execute_many_dict('''
                SELECT id
                FROM job
                WHERE build_id = %s AND project_id = %s
            ''', [build_id, project_id])

            user_id = get_mcp_user_id()
            for j in jobs:
                g.db.execute('''
                    INSERT INTO abort(job_id, user_id) VALUES(%s, %s)
                ''', [j['id'], user_id])
            g.db.commit()

            audit_mcp('abort_build', outcome='success',
                      details={'project_id': project_id, 'build_id': build_id,
                               'aborted_count': len(jobs)})
            return {'message': 'Aborted %d job(s)' % len(jobs), 'status': 200}, 200
        except Exception as exc:
            audit_mcp('abort_build', outcome='failure',
                      details={'project_id': project_id, 'build_id': build_id},
                      error=str(exc))
            raise
