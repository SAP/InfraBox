from flask import g, abort
from flask_restplus import Resource

from pyinfraboxutils.ibflask import auth_token_required, OK
from pyinfraboxutils.storage import storage

from dashboard_api import project_ns as ns

def restart_build(project_id, build_id):
    user_id = g.token['user']['id']

    build = g.db.execute_one_dict('''
        SELECT b.*
        FROM build b
        INNER JOIN collaborator co
            ON b.id = %s
            AND b.project_id = co.project_id
            AND co.project_id = %s
            AND co.user_id = %s
    ''', [build_id, project_id, user_id])

    if not build:
        abort(404)


    result = g.db.execute_one_dict('''
        SELECT max(restart_counter) as restart_counter
        FROM build WHERE build_number = $1 and project_id = $2
    ''', [build['build_number'], project_id])

    restart_counter = result.restart_counter + 1

    result = g.db.execute_one_dict('''
        INSERT INTO build (commit_id, build_number,
                           project_id, restart_counter, source_upload_id)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    ''', [build['commit_id'],
          build['build_number'],
          project_id,
          restart_counter,
          build['source_upload_id']])

    new_build_id = result['id']

    job = g.db.execute_one_dict('''
           SELECT repo, env_var FROM job
           WHERE project_id = %s
           AND name = 'Create Jobs'
           AND build_id = %s
    ''', [project_id, build_id])

    g.db.execute('''
        INSERT INTO job (id, state, build_id, type,
            name, cpu, memory, project_id, build_only, dockerfile, repo, env_var, definition)
        VALUES (gen_random_uuid(), 'queued', %s, 'create_job_matrix',
                'Create Jobs', 1, 1024, %s, false, '', %s, %s, %s);
    ''', [new_build_id, project_id, job['repo'], job['env_var'], job['definition']])
    g.db.commit()


@ns.route('/<project_id>/builds/<build_id>/restart')
class BuildRestart(Resource):

    @auth_token_required(['user'])
    def get(self, project_id, build_id):
        restart_build(project_id, build_id)
        return OK('Aborted all jobs')


@ns.route('/<project_id>/builds/<build_id>/abort')
class BuildAbort(Resource):

    @auth_token_required(['user'])
    def get(self, project_id, build_id):
        jobs = g.db.execute_many_dict('''
            SELECT id
            FROM job
            WHERE build_id = %s
                AND project_id = %s
        ''', [build_id, project_id])


        for j in jobs:
            g.db.execute('''
                INSERT INTO abort(job_id) VALUES(%s)
            ''', [j['id']])

        g.db.commit()

        return OK('Aborted all jobs')

@ns.route('/<project_id>/builds/<build_id>/cache/clear')
class BuildCacheClear(Resource):

    @auth_token_required(['user'])
    def get(self, project_id, build_id):
        jobs = g.db.execute_many_dict('''
            SELECT j.name, branch from job j
            INNER JOIN build b
                ON b.id = j.build_id
                AND j.project_id = b.project_id
            LEFT OUTER JOIN "commit" c
                ON b.commit_id = c.id
                AND c.project_id = b.project_id
            WHERE
                b.id = %s AND
                j.project_id = %s
        ''', [build_id, project_id])

        for j in jobs:
            key = 'project_%s_branch_%s_job_%s.tar.gz' % (project_id, j['branch'], j['name'])
            storage.delete_cache(key)

        return OK('Cleared cache')
