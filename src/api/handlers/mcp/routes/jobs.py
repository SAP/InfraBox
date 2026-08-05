"""
MCP job endpoints.
GET    /api/v1/mcp/projects/<project_id>/builds/<build_id>/jobs
GET    /api/v1/mcp/projects/<project_id>/jobs/<job_id>
GET    /api/v1/mcp/projects/<project_id>/jobs/<job_id>/log
GET    /api/v1/mcp/projects/<project_id>/jobs/<job_id>/artifacts
GET    /api/v1/mcp/projects/<project_id>/jobs/<job_id>/stats
GET    /api/v1/mcp/projects/<project_id>/jobs/<job_id>/testruns
GET    /api/v1/mcp/projects/<project_id>/jobs/<job_id>/manifest
POST   /api/v1/mcp/projects/<project_id>/jobs/<job_id>/restart
POST   /api/v1/mcp/projects/<project_id>/jobs/<job_id>/rerun
DELETE /api/v1/mcp/projects/<project_id>/jobs/<job_id>/abort
"""
import json
import logging
import re
import uuid as _uuid

from flask import g, request, abort
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
from api.handlers.mcp.pagination import parse_pagination, page

logger = logging.getLogger('mcp_jobs')

_ACCESS_DENIED = 'access to this project is not permitted for the current MCP token'
_JOB_BY_PROJECT = 'SELECT id FROM job WHERE id = %s AND project_id = %s'

# Log byte caps: bound get_job_log so one call can't overflow the context.
DEFAULT_LOG_BYTES = 1024 * 1024      # 1 MB tail by default
MAX_LOG_BYTES = 5 * 1024 * 1024      # 5 MB hard ceiling per request

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
        """List jobs for a build.

        Paginated (default limit 50). Optional ?state= filters by job state
        (e.g. failure). Returns {items, total, limit, offset}.
        """
        audit_mcp('list_jobs', outcome='attempt',
                  details={'project_id': project_id, 'build_id': build_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('list_jobs', outcome='forbidden', details={'project_id': project_id})
            abort(403, _ACCESS_DENIED)

        limit, offset = parse_pagination()
        state = request.args.get('state') or None

        # Build the WHERE clause; state is an optional, exact-match filter.
        where = 'j.build_id = %s AND j.project_id = %s'
        params = [build_id, project_id]
        if state:
            where += ' AND j.state = %s'
            params.append(state)

        try:
            total = g.db.execute_one_dict(
                'SELECT count(*) AS c FROM job j WHERE ' + where, params)['c']
            rows = g.db.execute_many_dict('''
                SELECT j.id, j.name, j.state, j.build_id, j.project_id,
                       j.start_date, j.end_date, j.message
                FROM job j
                WHERE ''' + where + '''
                ORDER BY j.name
                LIMIT %s OFFSET %s
            ''', params + [limit, offset])
            items = [_job_dict(r) for r in rows]
            audit_mcp('list_jobs', outcome='success',
                      details={'project_id': project_id, 'build_id': build_id,
                               'count': len(items), 'total': total})
            return page(items, total, limit, offset)
        except Exception as exc:
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
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
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
            audit_mcp('get_job', outcome='failure',
                      details={'project_id': project_id, 'job_id': job_id}, error=str(exc))
            raise


@ns_job.route('/log')
class MCPJobLog(Resource):
    @mcp_auth_required
    @mcp_rate_limit('get_job_log')
    def get(self, project_id, job_id):
        """Get console log for a job.

        Bounded by default: returns at most the last DEFAULT_LOG_BYTES (1 MB) of
        the log so a single call cannot overflow the client/model context.
        Query params:
          - max_bytes: cap on returned bytes (default 1 MB, max 5 MB)
          - offset/length: read an explicit byte range instead of the tail
        Returns {log, total_bytes, offset, length, truncated}.
        """
        audit_mcp('get_job_log', outcome='attempt',
                  details={'project_id': project_id, 'job_id': job_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('get_job_log', outcome='forbidden', details={'project_id': project_id})
            abort(403, _ACCESS_DENIED)

        job = g.db.execute_one_dict(_JOB_BY_PROJECT, [job_id, project_id])
        if not job:
            abort(404)

        try:
            # Two-stage lookup mirroring legacy /console endpoint:
            # 1) prefer the archived job.console column (scheduler moves logs there on
            #    job termination and DELETEs the streaming rows)
            # 2) fall back to the console table (for jobs still running)
            archived = g.db.execute_one_dict('''
                SELECT console FROM job WHERE id = %s AND project_id = %s
            ''', [job_id, project_id])

            if archived and archived['console']:
                log = archived['console']
            else:
                rows = g.db.execute_many_dict('''
                    SELECT output FROM console WHERE job_id = %s ORDER BY date
                ''', [job_id])
                log = ''.join(r['output'] for r in rows)

            sliced = _slice_log(log)
            audit_mcp('get_job_log', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id,
                               'total_bytes': sliced['total_bytes'],
                               'returned_bytes': sliced['length'],
                               'truncated': sliced['truncated']})
            return sliced
        except Exception as exc:
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
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
            # `archive` is a jsonb[] column on the job table (see migration 00009.sql),
            # NOT a standalone table. Legacy /archive endpoint reads it this way.
            row = g.db.execute_one_dict('''
                SELECT archive
                FROM job
                WHERE id = %s AND project_id = %s
            ''', [job_id, project_id])

            archive = (row or {}).get('archive') or []
            all_items = [{'filename': a.get('filename'),
                          'filesize': a.get('size') or a.get('filesize')}
                         for a in archive]
            # archive is a single jsonb[] column (already in memory), so paginate
            # by slicing the list rather than in SQL.
            limit, offset = parse_pagination()
            total = len(all_items)
            items = all_items[offset:offset + limit]
            audit_mcp('list_job_artifacts', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id,
                               'count': len(items), 'total': total})
            return page(items, total, limit, offset)
        except Exception as exc:
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
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
                except Exception as parse_exc:
                    logger.warning('failed to parse stats for job %s: %s', job_id, parse_exc)
                    audit_mcp('get_job_stats', outcome='partial',
                              details={'project_id': project_id, 'job_id': job_id},
                              error=str(parse_exc))
                    return result
            audit_mcp('get_job_stats', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id})
            return result
        except Exception as exc:
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
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
            limit, offset = parse_pagination()
            total = g.db.execute_one_dict('''
                SELECT count(*) AS c FROM test_run tr
                WHERE tr.job_id = %s AND tr.project_id = %s
            ''', [job_id, project_id])['c']
            rows = g.db.execute_many_dict('''
                SELECT tr.state, tr.name, tr.suite, tr.duration, tr.message, tr.stack,
                       to_char(tr.timestamp, 'YYYY-MM-DD HH24:MI:SS') AS timestamp
                FROM test_run tr
                WHERE tr.job_id = %s AND tr.project_id = %s
                ORDER BY tr.suite, tr.name
                LIMIT %s OFFSET %s
            ''', [job_id, project_id, limit, offset])
            audit_mcp('get_job_testruns', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id,
                               'count': len(rows), 'total': total})
            return page(rows, total, limit, offset)
        except Exception as exc:
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
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
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
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


def _slice_log(log):
    """Bound a job log to a byte window.

    Default (no params): return the LAST DEFAULT_LOG_BYTES of the log — the tail
    is where failures/stack traces live, and it's what's useful when truncating.
    Query params:
      - max_bytes: cap the returned size (clamped to [1, MAX_LOG_BYTES])
      - offset/length: read an explicit byte range from the start instead of the tail
    Returns {log, total_bytes, offset, length, truncated}.
    """
    data = (log or '').encode('utf-8')
    total = len(data)

    raw_offset = request.args.get('offset')
    raw_length = request.args.get('length')
    raw_max = request.args.get('max_bytes')

    if raw_offset is not None or raw_length is not None:
        # Explicit range read from the start of the log.
        offset = _pos_int('offset', raw_offset, 0)
        length = _pos_int('length', raw_length, DEFAULT_LOG_BYTES)
        length = min(length, MAX_LOG_BYTES)
        chunk = data[offset:offset + length]
    else:
        # Default: tail of the log, capped by max_bytes.
        max_bytes = _pos_int('max_bytes', raw_max, DEFAULT_LOG_BYTES)
        max_bytes = min(max(max_bytes, 1), MAX_LOG_BYTES)
        offset = max(0, total - max_bytes)
        chunk = data[offset:]
        length = max_bytes

    text = chunk.decode('utf-8', errors='replace')
    return {
        'log': text,
        'total_bytes': total,
        'offset': offset,
        'length': len(chunk),
        'truncated': offset > 0 or (offset + len(chunk)) < total,
    }


def _pos_int(name, raw, default):
    if raw is None or raw == '':
        return default
    try:
        v = int(raw)
    except (TypeError, ValueError):
        abort(400, '%s must be an integer' % name)
    if v < 0:
        abort(400, '%s must be >= 0' % name)
    return v


def _compact_stats(series):
    """Downsample a stats time series to at most 100 points."""
    if not isinstance(series, list) or len(series) <= 100:
        return series
    step = len(series) // 100
    return series[::step]


# ────────────────────────────────────────────────────────────────────────────
# Shared write-path helpers (restart / rerun)
# ────────────────────────────────────────────────────────────────────────────

_RESTARTABLE_STATES = ('error', 'failure', 'finished', 'killed', 'unstable')
_RESTARTABLE_TYPES = ('run_project_container', 'run_docker_compose')


def _clone_jobs_and_bump_names(build_jobs, restart_ids, single_id=None):
    """Clone the specified jobs, mark originals as restarted, and re-wire dependencies.

    Args:
        build_jobs: rows from `SELECT id, dependencies, restarted, state FROM job WHERE build_id`
        restart_ids: list of job ids that should be marked as restarted
        single_id: if given (rerun mode), only this one is cloned (dependencies get re-wired
            in downstream jobs but only this one gets a new row inserted)

    Returns:
        (jobs_to_insert, old_id_job_map). old_id_job_map maps old-id → cloned-row (with new id/name)
        for dependency rewriting in the second pass.
    """
    # Load the full job rows for the ones we plan to touch.
    to_clone = restart_ids if single_id is None else [single_id]
    jobs = []
    for jid in to_clone:
        row = g.db.execute_one_dict('''
            SELECT id, build_id, type, dockerfile, name, project_id, dependencies,
                   repo, env_var, env_var_ref, build_arg, deployment, definition, cluster_name
            FROM job
            WHERE id = %s
        ''', [jid])
        if row:
            jobs.append(row)

    old_id_job = {}
    for j in jobs:
        # Mark the original as restarted so it won't be picked again.
        g.db.execute('UPDATE job SET restarted = true WHERE id = %s;', [j['id']])
        old_id_job[j['id']] = j
        j['id'] = str(_uuid.uuid4())

        # Bump the name suffix (`.1`, `.2`, ...) so the clone gets a unique name.
        parts = j['name'].split('/')
        last = parts[-1]
        m = re.search(r'(.*)\.([0-9]+)$', last)
        if m:
            n = int(m.group(2)) + 1
            front = '/'.join(parts[:-1])
            j['name'] = ('%s/%s.%d' % (front, m.group(1), n)) if front else '%s.%d' % (m.group(1), n)
        else:
            j['name'] = j['name'] + '.1'
    return jobs, old_id_job


def _restart_or_rerun_job(project_id, job_id, rerun_only, msg_who):
    """Shared core for MCP restart_job and rerun_job.

    Args:
        project_id, job_id: target
        rerun_only: if True, only the target job is cloned (dependents are NOT restarted).
                    if False, target job + all downstream dependents are cloned.
        msg_who: string inserted into the audit console message

    Returns dict payload for the JSON response.
    """
    job = g.db.execute_one_dict('''
        SELECT state, type, build_id, restarted, dependencies, name
        FROM job
        WHERE id = %s AND project_id = %s
    ''', [job_id, project_id])
    if not job:
        abort(404)

    if job['type'] not in _RESTARTABLE_TYPES:
        abort(400, 'Job type cannot be restarted')
    if job['state'] not in _RESTARTABLE_STATES:
        abort(400, 'Job in state %s cannot be restarted' % job['state'])
    if job['restarted']:
        abort(400, 'This job has been already restarted')

    build_id = job['build_id']

    # Bug F fix: take a row lock on the build so two concurrent restarts of jobs
    # in the same build cannot both read the same build_jobs snapshot and clone
    # overlapping downstream dependents. Held until commit at the end of this fn.
    g.db.execute('SELECT id FROM build WHERE id = %s FOR UPDATE', [build_id])

    # Bug B fix: atomically claim the target job via compare-and-set. Only the
    # first concurrent request flips restarted false->true and gets a row back;
    # a second concurrent request matches 0 rows and aborts cleanly. This replaces
    # the earlier read-then-check TOCTOU (the guard above is only a fast-path).
    claimed = g.db.execute_one_dict('''
        UPDATE job SET restarted = true
        WHERE id = %s AND project_id = %s AND restarted = false
        RETURNING id
    ''', [job_id, project_id])
    if not claimed:
        abort(409, 'Job %s has already been restarted by a concurrent request' % job_id)

    # For rerun_only, additionally require that upstream deps aren't still running.
    if rerun_only:
        for dep in (job['dependencies'] or []):
            p = g.db.execute_one_dict('''
                SELECT state FROM job WHERE id = %s AND project_id = %s
            ''', [dep['job-id'], project_id])
            if p and p['state'] in ('queued', 'running'):
                abort(400, 'Job %s has an executing parent job' % job_id)

    # Gather all jobs in the build (for downstream propagation and safety checks).
    build_jobs = g.db.execute_many_dict('''
        SELECT state, id, dependencies, restarted
        FROM job
        WHERE build_id = %s AND project_id = %s
    ''', [build_id, project_id])

    # Compute the set to mark-restarted:
    #  - restart_job: closure of the target + all transitive downstream dependents
    #  - rerun_job:   just the target
    restart_ids = [job_id]
    if not rerun_only:
        while True:
            found = False
            for j in build_jobs:
                if j['id'] in restart_ids:
                    continue
                if not j['dependencies'] or j['restarted']:
                    continue
                for dep in j['dependencies']:
                    if dep['job-id'] in restart_ids:
                        restart_ids.append(j['id'])
                        found = True
                        break
            if not found:
                break

    # Safety: none of the affected jobs may be running/scheduled.
    ok_states = _RESTARTABLE_STATES + ('skipped', 'queued')
    for j in build_jobs:
        if j['id'] in restart_ids and j['state'] not in ok_states:
            abort(400, 'Some child jobs are still running')

    single_id = job_id if rerun_only else None
    jobs, old_id_job = _clone_jobs_and_bump_names(build_jobs, restart_ids, single_id=single_id)

    # In restart mode, rewire dependencies among cloned jobs.
    # In rerun mode, only the target is cloned so no dependency rewiring is needed on jobs.
    if not rerun_only:
        for j in jobs:
            for dep in (j['dependencies'] or []):
                if dep['job-id'] in old_id_job:
                    dep['job'] = old_id_job[dep['job-id']]['name']
                    dep['job-id'] = old_id_job[dep['job-id']]['id']

    msg = 'Job restarted by %s\n' % msg_who
    for j in jobs:
        g.db.execute('''
            INSERT INTO job (state, id, build_id, type, dockerfile, name, project_id, dependencies, repo,
                             env_var, env_var_ref, build_arg, deployment, definition, restarted, cluster_name)
            VALUES ('queued', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false, %s);
            INSERT INTO console (job_id, output) VALUES (%s, %s);
        ''', [j['id'], j['build_id'], j['type'], j['dockerfile'], j['name'], j['project_id'],
              json.dumps(j['dependencies']),
              json.dumps(j['repo']),
              json.dumps(j['env_var']),
              json.dumps(j['env_var_ref']),
              json.dumps(j['build_arg']),
              json.dumps(j['deployment']),
              json.dumps(j['definition']),
              j['cluster_name'],
              j['id'],
              msg])
    g.db.commit()
    return {
        'job_id': jobs[0]['id'] if jobs else None,
        'cloned_count': len(jobs),
        'status': 200,
    }


# ────────────────────────────────────────────────────────────────────────────
# MCP write endpoints
# ────────────────────────────────────────────────────────────────────────────


@ns_job.route('/restart')
class MCPJobRestart(Resource):
    @mcp_auth_required
    @mcp_rate_limit('trigger_build')  # share the trigger bucket for all write ops
    def post(self, project_id, job_id):
        """Restart a job AND its downstream dependents. Requires allow_trigger."""
        audit_mcp('restart_job', outcome='attempt',
                  details={'project_id': project_id, 'job_id': job_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('restart_job', outcome='forbidden', details={'project_id': project_id})
            abort(403, _ACCESS_DENIED)
        if not check_trigger_access_mcp():
            audit_mcp('restart_job', outcome='forbidden',
                      details={'project_id': project_id, 'job_id': job_id,
                               'reason': 'trigger not allowed'})
            abort(403, 'this MCP token does not have trigger permission')

        try:
            msg_who = 'MCP token (user %s)' % get_mcp_user_id()
            result = _restart_or_rerun_job(project_id, job_id, rerun_only=False, msg_who=msg_who)
            audit_mcp('restart_job', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id,
                               'cloned_count': result.get('cloned_count')})
            return result, 200
        except Exception as exc:
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
            audit_mcp('restart_job', outcome='failure',
                      details={'project_id': project_id, 'job_id': job_id},
                      error=str(exc))
            raise


@ns_job.route('/rerun')
class MCPJobRerun(Resource):
    @mcp_auth_required
    @mcp_rate_limit('trigger_build')  # share the trigger bucket
    def post(self, project_id, job_id):
        """Rerun a single job WITHOUT restarting its downstream dependents.
        Most common AI use case: 'retry just this failed step'. Requires allow_trigger."""
        audit_mcp('rerun_job', outcome='attempt',
                  details={'project_id': project_id, 'job_id': job_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('rerun_job', outcome='forbidden', details={'project_id': project_id})
            abort(403, _ACCESS_DENIED)
        if not check_trigger_access_mcp():
            audit_mcp('rerun_job', outcome='forbidden',
                      details={'project_id': project_id, 'job_id': job_id,
                               'reason': 'trigger not allowed'})
            abort(403, 'this MCP token does not have trigger permission')

        try:
            msg_who = 'MCP token (user %s)' % get_mcp_user_id()
            result = _restart_or_rerun_job(project_id, job_id, rerun_only=True, msg_who=msg_who)
            audit_mcp('rerun_job', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id,
                               'cloned_count': result.get('cloned_count')})
            return result, 200
        except Exception as exc:
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
            audit_mcp('rerun_job', outcome='failure',
                      details={'project_id': project_id, 'job_id': job_id},
                      error=str(exc))
            raise


@ns_job.route('/abort')
class MCPJobAbort(Resource):
    @mcp_auth_required
    @mcp_rate_limit('trigger_build')  # share the trigger bucket
    def delete(self, project_id, job_id):
        """Abort a single running job. Requires allow_trigger on the MCP token."""
        audit_mcp('abort_job', outcome='attempt',
                  details={'project_id': project_id, 'job_id': job_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('abort_job', outcome='forbidden', details={'project_id': project_id})
            abort(403, _ACCESS_DENIED)
        if not check_trigger_access_mcp():
            audit_mcp('abort_job', outcome='forbidden',
                      details={'project_id': project_id, 'job_id': job_id,
                               'reason': 'trigger not allowed'})
            abort(403, 'this MCP token does not have trigger permission')

        # Confirm the job exists in this project before writing the abort row.
        job = g.db.execute_one_dict(_JOB_BY_PROJECT, [job_id, project_id])
        if not job:
            abort(404)

        try:
            g.db.execute('''
                INSERT INTO abort(job_id, user_id) VALUES(%s, %s)
            ''', [job_id, get_mcp_user_id()])
            g.db.commit()
            audit_mcp('abort_job', outcome='success',
                      details={'project_id': project_id, 'job_id': job_id})
            return {'message': 'Successfully aborted job', 'status': 200}, 200
        except Exception as exc:
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
            audit_mcp('abort_job', outcome='failure',
                      details={'project_id': project_id, 'job_id': job_id},
                      error=str(exc))
            raise
