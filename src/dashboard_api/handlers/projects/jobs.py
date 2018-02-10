import json

from flask import g, abort
from flask_restplus import Resource

from pyinfraboxutils.ibflask import auth_required, OK
from pyinfraboxutils.storage import storage

from dashboard_api.namespaces import project as ns

@ns.route('/<project_id>/jobs/<job_id>/restart')
class JobRestart(Resource):

    @auth_required(['user'])
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

    @auth_required(['user'])
    #pylint: disable=unused-argument
    def get(self, project_id, job_id):
        g.db.execute('''
            INSERT INTO abort(job_id) VALUES(%s)
        ''', [job_id])
        g.db.commit()

        return OK('Successfully aborted job')

@ns.route('/<project_id>/jobs/<job_id>/testresults')
class Testresults(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
        result = g.db.execute_many_dict('''
            SELECT tr.state, t.name, t.suite, tr.duration, t.build_number, tr.message, tr.stack
            FROM test t
            INNER JOIN test_run tr
                ON t.id = tr.test_id
                AND t.project_id = tr.project_id
            WHERE   tr.project_id = %s
                AND tr.job_id = %s
        ''', [project_id, job_id])

        return result

@ns.route('/<project_id>/jobs/<job_id>/tabs')
class Tabs(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
        result = g.db.execute_many_dict('''
            SELECT name, data, type
            FROM job_markup
            WHERE   job_id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        return result

@ns.route('/<project_id>/jobs/<job_id>/console')
class Console(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
        result = g.db.execute_one_dict('''
            SELECT console
            FROM job
            WHERE   id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        if not result:
            abort(404)

        if not result['console']:
            abort(404)

        return result['console']

@ns.route('/<project_id>/jobs/<job_id>/console')
class Output(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
        # TODO
        assert False


@ns.route('/<project_id>/jobs/<job_id>/badges')
class Badges(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
        result = g.db.execute_many_dict('''
            SELECT subject, status, color
            FROM job_badge
            WHERE   job_id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        return result

@ns.route('/<project_id>/jobs/<job_id>/stats')
class Stats(Resource):

    @auth_required(['user'], allow_if_public=True)
    def get(self, project_id, job_id):
        result = g.db.execute_one_dict('''
            SELECT stats
            FROM job
            WHERE   id = %s
                AND project_id = %s
        ''', [job_id, project_id])

        if not result:
            abort(404)

        if not result['stats']:
            return {}
        else:
            return json.loads(result['stats'])

@ns.route('/<project_id>/jobs/<job_id>/cache/clear')
class JobCacheClear(Resource):

    @auth_required(['user'])
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
