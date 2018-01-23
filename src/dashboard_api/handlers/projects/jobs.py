from flask import g, abort
from flask_restplus import Resource

from pyinfraboxutils.ibflask import auth_token_required, OK
from pyinfraboxutils.storage import storage

from dashboard_api import project_ns as ns

@ns.route('/<project_id>/jobs/<job_id>/restart')
class JobRestart(Resource):

    @auth_token_required(['user'])
    def get(self, project_id, job_id):

        job = g.db.execute_many_dict('''
            SELECT state, type
            FROM job
            WHERE id = %s
            AND project_id = %s
        ''', [job_id, project_id])

        if not job:
            abort(404)

        job_type = job['type']
        job_state = job['state']

        if job_type not in ('run_project_container', 'run_docker_compose'):
            abort(400, 'Job type cannot be restarted')

        if job_state not in ('error', 'failure', 'finished', 'killed'):
            abort(400, 'Job in state %s cannot be restarted' % job_state)

        g.db.execute('''
            UPDATE job SET state = 'queued', console = null WHERE id = %s
        ''', [job_id])
        g.db.commit()

        return OK('Successfully restarted job')

@ns.route('/<project_id>/jobs/<job_id>/abort')
class JobAbort(Resource):

    @auth_token_required(['user'])
    def get(self, project_id, job_id):
        g.db.execute('''
            INSERT INTO abort(job_id) VALUES(%s)
        ''', [job_id])
        g.db.commit()

        return OK('Successfully aborted job')

@ns.route('/<project_id>/jobs/<job_id>/cache/clear')
class JobCacheClear(Resource):

    @auth_token_required(['user'])
    def get(self, project_id, job_id):
        job = g.db.execute_one_dict('''
            SELECT j.name, branch from job j
            INNER JOIN build b
                ON b.id = j.build_id
                AND j.project_id = b.project_id
            LEFT OUTER JOIN "commit" c
                ON b.commit_id = c.id
                AND c.project_id = b.project_id
            WHERE
                j.id = %s AND
                j.project_id = %s
        ''', [job_id, project_id])

        if not job:
            abort(404)

        key = 'project_%s_branch_%s_job_%s.tar.gz' % (project_id, job['branch'], job['name'])
        storage.delete_cache(key)

        return OK('Cleared cache')
