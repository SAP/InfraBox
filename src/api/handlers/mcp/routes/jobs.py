"""
MCP job endpoints.
GET /api/v1/mcp/projects/<project_id>/builds/<build_id>/jobs
GET /api/v1/mcp/projects/<project_id>/jobs/<job_id>
GET /api/v1/mcp/projects/<project_id>/jobs/<job_id>/log
GET /api/v1/mcp/projects/<project_id>/jobs/<job_id>/artifacts
GET /api/v1/mcp/projects/<project_id>/jobs/<job_id>/stats
GET /api/v1/mcp/projects/<project_id>/jobs/<job_id>/testruns
GET /api/v1/mcp/projects/<project_id>/jobs/<job_id>/manifest
"""
import json

from flask import g, abort
from flask_restx import Resource

from pyinfraboxutils.ibrestplus import api
from api.handlers.mcp.auth import mcp_auth_required, check_project_access_mcp
from api.handlers.mcp.rate_limit import mcp_rate_limit
from api.handlers.mcp.audit import audit_mcp

_ACCESS_DENIED = 'access to this project is not permitted for the current MCP token'
_JOB_BY_PROJECT = 'SELECT id FROM job WHERE id = %s AND project_id = %s'

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
            abort(403, _ACCESS_DENIED)

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


@ns_job.route('')
class MCPJob(Resource):
    @mcp_auth_required
    @mcp_rate_limit('list_jobs')
    def get(self, project_id, job_id):
        """Get a single job by ID."""
        audit_mcp('get_job', outcome='attempt',
                  details={'project_id': project_id, 'job_id': job_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('get_job', outcome='forbidden', details={'project_id': project_id})
            abort(403, _ACCESS_DENIED)

        try:
            row = g.db.execute_one_dict('''
                SELECT j.id, j.name, j.state, j.build_id, j.project_id,
                       j.start_date, j.end_date, j.message
                FROM job j
                WHERE j.id = %s AND j.project_id = %s
            ''', [job_id, project_id])
            if not row:
                abort(404)
            audit_mcp('get_job', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id})
            return _job_dict(row)
        except Exception as exc:
            audit_mcp('get_job', outcome='failure',
                      details={'project_id': project_id, 'job_id': job_id}, error=str(exc))
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
            abort(403, _ACCESS_DENIED)

        job = g.db.execute_one_dict(_JOB_BY_PROJECT, [job_id, project_id])
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
            abort(403, _ACCESS_DENIED)

        job = g.db.execute_one_dict(_JOB_BY_PROJECT, [job_id, project_id])
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


@ns_job.route('/stats')
class MCPJobStats(Resource):
    @mcp_auth_required
    @mcp_rate_limit('list_jobs')
    def get(self, project_id, job_id):
        """Get resource usage stats for a job."""
        audit_mcp('get_job_stats', outcome='attempt',
                  details={'project_id': project_id, 'job_id': job_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('get_job_stats', outcome='forbidden', details={'project_id': project_id})
            abort(403, _ACCESS_DENIED)

        try:
            row = g.db.execute_one_dict('''
                SELECT stats FROM job WHERE id = %s AND project_id = %s
            ''', [job_id, project_id])
            if not row:
                abort(404)
            result = {}
            if row.get('stats'):
                try:
                    parsed = json.loads(row['stats'])
                    for k, v in parsed.items():
                        result[k] = _compact_stats(v)
                except Exception:
                    pass
            audit_mcp('get_job_stats', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id})
            return result
        except Exception as exc:
            audit_mcp('get_job_stats', outcome='failure',
                      details={'project_id': project_id, 'job_id': job_id}, error=str(exc))
            raise


@ns_job.route('/testruns')
class MCPJobTestruns(Resource):
    @mcp_auth_required
    @mcp_rate_limit('list_jobs')
    def get(self, project_id, job_id):
        """Get test results for a job."""
        audit_mcp('get_job_testruns', outcome='attempt',
                  details={'project_id': project_id, 'job_id': job_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('get_job_testruns', outcome='forbidden', details={'project_id': project_id})
            abort(403, _ACCESS_DENIED)

        try:
            rows = g.db.execute_many_dict('''
                SELECT tr.state, tr.name, tr.suite, tr.duration, tr.message, tr.stack,
                       to_char(tr.timestamp, 'YYYY-MM-DD HH24:MI:SS') AS timestamp
                FROM test_run tr
                WHERE tr.job_id = %s AND tr.project_id = %s
            ''', [job_id, project_id])
            audit_mcp('get_job_testruns', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id, 'count': len(rows)})
            return rows
        except Exception as exc:
            audit_mcp('get_job_testruns', outcome='failure',
                      details={'project_id': project_id, 'job_id': job_id}, error=str(exc))
            raise


@ns_job.route('/manifest')
class MCPJobManifest(Resource):
    @mcp_auth_required
    @mcp_rate_limit('list_jobs')
    def get(self, project_id, job_id):
        """Get the infrabox.json manifest used for a job."""
        audit_mcp('get_job_manifest', outcome='attempt',
                  details={'project_id': project_id, 'job_id': job_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('get_job_manifest', outcome='forbidden', details={'project_id': project_id})
            abort(403, _ACCESS_DENIED)

        try:
            row = g.db.execute_one_dict('''
                SELECT j.name, j.start_date, j.end_date,
                       definition#>'{resources,limits,cpu}' AS cpu,
                       definition#>'{resources,limits,memory}' AS memory,
                       j.state, j.id, b.build_number, j.env_var, c.root_url
                FROM job j
                JOIN build b ON b.id = j.build_id AND b.project_id = j.project_id
                JOIN cluster c ON j.cluster_name = c.name
                WHERE j.id = %s AND j.project_id = %s
            ''', [job_id, project_id])
            if not row:
                abort(404)

            root_url = row['root_url']
            image = (root_url + '/' + project_id + '/' + row['name']
                     + ':build_' + str(row['build_number']))
            image = image.replace('https://', '').replace('http://', '').replace('//', '/')

            result = {
                'name': row['name'],
                'start_date': row['start_date'].isoformat() if row.get('start_date') else None,
                'end_date': row['end_date'].isoformat() if row.get('end_date') else None,
                'cpu': row['cpu'],
                'memory': row['memory'],
                'state': row['state'],
                'id': row['id'],
                'build_number': row['build_number'],
                'environment': row['env_var'],
                'image': image,
                'output': {
                    'url': (root_url + '/api/v1/projects/' + project_id
                            + '/jobs/' + job_id + '/output'),
                    'format': 'tar.snappy',
                },
            }
            audit_mcp('get_job_manifest', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id})
            return result
        except Exception as exc:
            audit_mcp('get_job_manifest', outcome='failure',
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


def _compact_stats(series):
    """Downsample a stats time series to at most 100 points."""
    if not isinstance(series, list) or len(series) <= 100:
        return series
    step = len(series) // 100
    return series[::step]
