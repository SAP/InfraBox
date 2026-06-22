"""
MCP job endpoints.
GET /api/v1/mcp/projects/<project_id>/builds/<build_id>/jobs
GET /api/v1/mcp/projects/<project_id>/jobs/<job_id>/log
GET /api/v1/mcp/projects/<project_id>/jobs/<job_id>/artifacts
"""
from flask import g, abort
from flask_restx import Resource

from pyinfraboxutils.ibrestplus import api
from api.handlers.mcp.auth import mcp_auth_required, check_project_access_mcp
from api.handlers.mcp.rate_limit import mcp_rate_limit
from api.handlers.mcp.audit import audit_mcp

ns_build_jobs = api.namespace('MCP Build Jobs',
                              path='/api/v1/mcp/projects/<project_id>/builds/<build_id>',
                              description='MCP job list')

ns_job = api.namespace('MCP Jobs',
                       path='/api/v1/mcp/projects/<project_id>/jobs/<job_id>',
                       description='MCP individual job operations')


@ns_build_jobs.route('/jobs')
class MCPJobList(Resource):
    @mcp_auth_required
    @mcp_rate_limit('list_jobs')
    def get(self, project_id, build_id):
        """List jobs for a build."""
        audit_mcp('list_jobs', outcome='attempt',
                  details={'project_id': project_id, 'build_id': build_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('list_jobs', outcome='forbidden', details={'project_id': project_id})
            abort(403, 'access to this project is not permitted for the current MCP token')

        try:
            rows = g.db.execute_many_dict('''
                SELECT j.id, j.name, j.state, j.build_id, j.project_id,
                       j.start_date, j.end_date, j.message
                FROM job j
                WHERE j.build_id = %s AND j.project_id = %s
                ORDER BY j.name
            ''', [build_id, project_id])
            result = [_job_dict(r) for r in rows]
            audit_mcp('list_jobs', outcome='success',
                      details={'project_id': project_id, 'build_id': build_id, 'count': len(result)})
            return result
        except Exception as exc:
            audit_mcp('list_jobs', outcome='failure',
                      details={'project_id': project_id, 'build_id': build_id}, error=str(exc))
            raise


@ns_job.route('/log')
class MCPJobLog(Resource):
    @mcp_auth_required
    @mcp_rate_limit('get_job_log')
    def get(self, project_id, job_id):
        """Get console log for a job."""
        audit_mcp('get_job_log', outcome='attempt',
                  details={'project_id': project_id, 'job_id': job_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('get_job_log', outcome='forbidden', details={'project_id': project_id})
            abort(403, 'access to this project is not permitted for the current MCP token')

        # Verify job belongs to project
        job = g.db.execute_one_dict('''
            SELECT id FROM job WHERE id = %s AND project_id = %s
        ''', [job_id, project_id])
        if not job:
            abort(404)

        try:
            rows = g.db.execute_many_dict('''
                SELECT output FROM console WHERE job_id = %s ORDER BY date
            ''', [job_id])
            log = ''.join(r['output'] for r in rows)
            audit_mcp('get_job_log', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id})
            return log, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        except Exception as exc:
            audit_mcp('get_job_log', outcome='failure',
                      details={'project_id': project_id, 'job_id': job_id}, error=str(exc))
            raise


@ns_job.route('/artifacts')
class MCPJobArtifacts(Resource):
    @mcp_auth_required
    @mcp_rate_limit('list_job_artifacts')
    def get(self, project_id, job_id):
        """List artifacts for a job."""
        audit_mcp('list_job_artifacts', outcome='attempt',
                  details={'project_id': project_id, 'job_id': job_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('list_job_artifacts', outcome='forbidden', details={'project_id': project_id})
            abort(403, 'access to this project is not permitted for the current MCP token')

        job = g.db.execute_one_dict('''
            SELECT id FROM job WHERE id = %s AND project_id = %s
        ''', [job_id, project_id])
        if not job:
            abort(404)

        try:
            rows = g.db.execute_many_dict('''
                SELECT filename, filesize, created_at
                FROM archive
                WHERE job_id = %s
                ORDER BY filename
            ''', [job_id])
            result = [{'filename': r['filename'],
                       'filesize': r.get('filesize'),
                       'created_at': r['created_at'].isoformat() if r.get('created_at') else None}
                      for r in rows]
            audit_mcp('list_job_artifacts', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id, 'count': len(result)})
            return result
        except Exception as exc:
            audit_mcp('list_job_artifacts', outcome='failure',
                      details={'project_id': project_id, 'job_id': job_id}, error=str(exc))
            raise


def _job_dict(r):
    return {
        'id': r['id'],
        'name': r['name'],
        'state': r['state'],
        'build_id': r['build_id'],
        'project_id': r['project_id'],
        'start_date': r['start_date'].isoformat() if r.get('start_date') else None,
        'end_date': r['end_date'].isoformat() if r.get('end_date') else None,
        'message': r.get('message'),
    }
