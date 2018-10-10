#pylint: disable=too-many-lines,too-few-public-methods,too-many-locals,too-many-statements,too-many-branches
import os
import json
import uuid
import copy
import urllib
import random
from datetime import datetime
from io import BytesIO

import requests

from flask import jsonify, request, send_file, g, after_this_request, abort
from flask_restplus import Resource

from werkzeug.datastructures import FileStorage

from pyinfrabox.utils import validate_uuid
from pyinfrabox.badge import validate_badge
from pyinfrabox.markup import validate_markup
from pyinfrabox.testresult import validate_result
from pyinfrabox import ValidationError

from pyinfraboxutils.token import encode_job_token
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.ibflask import app
from pyinfraboxutils.storage import storage
from pyinfraboxutils.secrets import decrypt_secret
from pyinfraboxutils import get_root_url

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def delete_file(path):
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as error:
            app.logger.warn("Failed to delete file: %s", error)

@api.route("/api/job/job", doc=False)
class Job(Resource):

    def get(self):
        job_id = g.token['job']['id']
        data = {}

        # get all the job details
        r = g.db.execute_one('''
            SELECT
                j.name,
                null,
                j.dockerfile,
                p.id,
                p.type,
                p.name,
                b.id,
                b.commit_id,
                b.source_upload_id,
                b.build_number,
                u.github_api_token,
                u.username,
                null,
                j.type,
                null,
                null,
                j.repo,
                null,
                j.state,
                null,
                j.env_var,
                j.env_var_ref,
                null,
                null,
                u.id,
                j.build_arg,
                j.deployment,
                null,
                b.restart_counter,
                j.definition
            FROM job j
            INNER JOIN build b
                ON j.build_id = b.id
                AND j.project_id = b.project_id
            INNER JOIN collaborator co
                ON co.project_id = j.project_id
                AND co.role = 'Owner'
            INNER JOIN "user" u
                ON co.user_id = u.id
            INNER JOIN project p
                ON co.project_id = p.id
            WHERE j.id = %s
        ''', [job_id])

        limits = {}
        definition = r[29]
        build_only = True

        if definition:
            limits = definition['resources']['limits']
            build_only = definition.get('build_only', True)

        data['job'] = {
            "id": job_id,
            "name": r[0],
            "dockerfile": r[2],
            "build_only": build_only,
            "type": r[13],
            "repo": r[16],
            "state": r[18],
            "cpu": limits.get('cpu', 1),
            "memory": limits.get('memory', 1024),
            "build_arguments": r[25],
            "definition": r[29]
        }

        state = data['job']['state']
        if state in ("finished", "error", "failure", "skipped", "killed", "unstable"):
            abort(409, 'job not running anymore')

        env_vars = r[20]
        env_var_refs = r[21]
        deployments = r[26]

        data['project'] = {
            "id": r[3],
            "type": r[4],
            "name": r[5],
        }

        data['build'] = {
            "id": r[6],
            "commit_id": r[7],
            "source_upload_id": r[8],
            "build_number": r[9],
            "restart_counter": r[28]
        }

        data['repository'] = {
            "owner": r[11],
            "name": None,
            "github_api_token": r[10],
            "private": False
        }

        data['commit'] = {
            "branch": None,
            "tag": None
        }

        pull_request_id = None
        if data['project']['type'] == 'github' or data['project']['type'] == 'gerrit':
            r = g.db.execute_one('''
                SELECT
                    r.clone_url, r.name, r.private
                FROM repository r
                WHERE r.project_id = %s
            ''', [data['project']['id']])

            data['repository']['clone_url'] = r[0]
            data['repository']['name'] = r[1]
            data['repository']['private'] = r[2]

            # A regular commit
            r = g.db.execute_one('''
                SELECT
                    c.branch, c.committer_name, c.tag, c.pull_request_id
                FROM commit c
                WHERE c.id = %s
                    AND c.project_id = %s
            ''', [data['build']['commit_id'], data['project']['id']])

            data['commit'] = {
                "id": data['build']['commit_id'],
                "branch": r[0],
                "committer_name": r[1],
                "tag": r[2]
            }
            pull_request_id = r[3]

        if data['project']['type'] == 'upload':
            r = g.db.execute_one('''
                SELECT filename FROM source_upload
                WHERE id = %s
            ''', [data['build']['source_upload_id']])

            data['source_upload'] = {
                "filename": r[0]
            }

        # get dependencies
        r = g.db.execute_many('''
              WITH RECURSIVE next_job(id, parent) AS (
                      SELECT j.id, (p->>'job-id')::uuid parent
                      FROM job j, jsonb_array_elements(j.dependencies) AS p
                      WHERE j.id = %s
                  UNION
                      SELECT j.id, (p->>'job-id')::uuid parent
                      FROM job j
                      LEFT JOIN LATERAL jsonb_array_elements(j.dependencies) AS p ON true,
                      next_job nj WHERE j.id = nj.parent
              )
              SELECT id, name, state, start_date, end_date, dependencies
              FROM job WHERE id IN (SELECT distinct id FROM next_job WHERE id != %s)
        ''', [data['job']['id'], data['job']['id']])

        data['dependencies'] = []

        for d in r:
            data['dependencies'].append({
                "id": d[0],
                "name": d[1],
                "state": d[2],
                "start_date": str(d[3]),
                "end_date": str(d[4]),
                "depends_on": d[5]
            })

        # get parents
        r = g.db.execute_many('''
          SELECT id, name FROM job where id
              IN (SELECT (deps->>'job-id')::uuid FROM job, jsonb_array_elements(job.dependencies) as deps WHERE id = %s)
        ''', [data['job']['id']])

        data['parents'] = []

        for d in r:
            data['parents'].append({
                "id": d[0],
                "name": d[1]
            })

        # get the secrets
        secrets = g.db.execute_many('''
             SELECT name, value
             FROM secret
             WHERE project_id = %s
        ''', [data['project']['id']])

        is_fork = data['job'].get('fork', False)
        def get_secret(name):
            if is_fork:
                abort(400, 'Access to secret %s is not allowed from a fork' % name)

            for ev in secrets:
                if ev[0] == name:
                    return decrypt_secret(ev[1])
            return None

        # Deployments
        data['deployments'] = []
        if deployments:
            for dep in deployments:
                if dep['type'] == 'docker-registry':
                    if 'password' not in dep:
                        data['deployments'].append(dep)
                        continue

                    secret_name = dep['password']['$secret']
                    secret = get_secret(secret_name)

                    if secret is None:
                        abort(400, "Secret %s not found" % secret_name)

                    dep['password'] = secret
                    data['deployments'].append(dep)
                elif dep['type'] == 'gcr':
                    service_account = dep['service_account']['$secret']
                    secret = get_secret(service_account)

                    if secret is None:
                        abort(400, "Secret %s not found" % service_account)

                    dep['service_account'] = secret
                    data['deployments'].append(dep)
                elif dep['type'] == 'ecr':
                    access_key_id_name = dep['access_key_id']['$secret']
                    secret = get_secret(access_key_id_name)

                    if secret is None:
                        abort(400, "Secret %s not found" % access_key_id_name)

                    dep['access_key_id'] = secret

                    secret_access_key_name = dep['secret_access_key']['$secret']
                    secret = get_secret(secret_access_key_name)

                    if secret is None:
                        abort(400, "Secret %s not found" % secret_access_key_name)

                    dep['secret_access_key'] = secret
                    data['deployments'].append(dep)
                else:
                    abort(400, "Unknown deployment type")

        # Registries
        data['registries'] = []
        definition = data['job']['definition']
        registries = None

        if definition:
            registries = definition.get('registries', None)

        if registries:
            for r in registries:
                if r['type'] == 'docker-registry':
                    secret_name = r['password']['$secret']
                    secret = get_secret(secret_name)

                    if secret is None:
                        abort(400, "Secret %s not found" % secret_name)

                    r['password'] = secret
                    data['registries'].append(r)
                elif r['type'] == 'gcr':
                    service_account = r['service_account']['$secret']
                    secret = get_secret(service_account)

                    if secret is None:
                        abort(400, "Secret %s not found" % service_account)

                    r['service_account'] = secret
                    data['registries'].append(r)
                elif r['type'] == 'ecr':
                    access_key_id_name = r['access_key_id']['$secret']
                    secret = get_secret(access_key_id_name)

                    if secret is None:
                        abort(400, "Secret %s not found" % access_key_id_name)

                    r['access_key_id'] = secret

                    secret_access_key_name = r['secret_access_key']['$secret']
                    secret = get_secret(secret_access_key_name)

                    if secret is None:
                        abort(400, "Secret %s not found" % secret_access_key_name)

                    r['secret_access_key'] = secret
                    data['registries'].append(r)
                else:
                    abort(400, "Unknown registry type")

        root_url = get_root_url("global")

        # Default env vars
        project_name = urllib.quote_plus(data['project']['name']).replace('+', '%20')
        job_name = urllib.quote_plus(data['job']['name']).replace('+', '%20')
        build_url = "%s/dashboard/#/project/%s/build/%s/%s" % (root_url,
                                                               project_name,
                                                               data['build']['build_number'],
                                                               data['build']['restart_counter'])
        job_url = "%s/dashboard/#/project/%s/build/%s/%s/job/%s" % (root_url,
                                                                    project_name,
                                                                    data['build']['build_number'],
                                                                    data['build']['restart_counter'],
                                                                    job_name)

        job_api_url = "%s/api/v1/projects/%s/jobs/%s" % (root_url,
                                                         data['project']['id'],
                                                         data['job']['id'])

        build_api_url = "%s/api/v1/projects/%s/builds/%s" % (root_url,
                                                             data['project']['id'],
                                                             data['build']['id'])

        data['env_vars'] = {
            "TERM": "xterm-256color",
            "INFRABOX_JOB_ID": data['job']['id'],
            "INFRABOX_JOB_URL": job_url,
            "INFRABOX_JOB_API_URL": job_api_url,
            "INFRABOX_BUILD_API_URL": build_api_url,
            "INFRABOX_BUILD_NUMBER": "%s" % data['build']['build_number'],
            "INFRABOX_BUILD_RESTART_COUNTER": "%s" % data['build']['restart_counter'],
            "INFRABOX_BUILD_URL": build_url,
        }

        data['secrets'] = {}

        if data['commit']['branch']:
            data['env_vars']['INFRABOX_GIT_BRANCH'] = data['commit']['branch']

        if data['commit']['tag']:
            data['env_vars']['INFRABOX_GIT_TAG'] = data['commit']['tag']

        if pull_request_id:
            data['env_vars']['INFRABOX_GITHUB_PULL_REQUEST'] = "true"

        if env_vars:
            for name, value in env_vars.iteritems():
                data['env_vars'][name] = str(value)

        if env_var_refs:
            for name, value in env_var_refs.iteritems():
                secret = get_secret(value)

                if secret is None:
                    abort(400, "Secret %s not found" % value)

                data['secrets'][name] = secret

        return jsonify(data)

@api.route("/api/job/source", doc=False)
class Source(Resource):

    def get(self):
        job_id = g.token['job']['id']
        project_id = g.token['project']['id']

        r = g.db.execute_one('''
            SELECT su.filename
            FROM
                source_upload su
            INNER JOIN build b
                ON b.source_upload_id = su.id
            INNER JOIN job j
                ON j.build_id = b.id
            WHERE
                j.id = %s AND
                b.project_id = %s AND
                j.project_id = %s
        ''', [job_id, project_id, project_id])


        filename = r[0]
        filename = filename.replace('/', '_')

        g.release_db()

        f = storage.download_source(filename)

        if not f:
            abort(404)

        return send_file(f)


@api.route("/api/job/cache", doc=False)
class Cache(Resource):

    def get(self):
        g.release_db()
        project_id = g.token['project']['id']
        job_name = g.token['job']['name']
        filename = request.args.get('filename', None)
        template = 'project_%s_job_%s_%s'
        key = template % (project_id, job_name, filename)
        key = key.replace('/', '_')

        f = storage.download_cache(key)

        if not f:
            abort(404)

        return send_file(f)

    def post(self):
        g.release_db()

        project_id = g.token['project']['id']
        job_name = g.token['job']['name']

        for f, _ in request.files.items():
            template = 'project_%s_job_%s_%s'
            key = template % (project_id, job_name, f)
            key = key.replace('/', '_')
            stream = request.files[f].stream
            storage.upload_cache(stream, key)

        return jsonify({})


@api.route("/api/job/archive", doc=False)
class Archive(Resource):

    def post(self):
        job_id = g.token['job']['id']

        j = g.db.execute_one_dict('''
            SELECT id
            FROM job
            WHERE id = %s
            AND (state = 'running' OR end_date > NOW() - INTERVAL '5 minutes')
        ''', [job_id])

        if not j:
            abort(401, 'Unauthorized')

        for f in request.files:
            stream = request.files[f].stream
            key = '%s/%s' % (job_id, f)
            storage.upload_archive(stream, key)
            size = stream.tell()

            archive = {
                'filename': f,
                'size': size
            }

            g.db.execute('''
                UPDATE job
                SET archive = archive || %s::jsonb
                WHERE id = %s
            ''', [json.dumps(archive), job_id])

        g.db.commit()

        return jsonify({"message": "File uploaded"})

@api.route("/api/job/output", doc=False)
class Output(Resource):

    def post(self):
        job_id = g.token['job']['id']

        for f, _ in request.files.items():
            key = "%s/%s" % (job_id, f)

            stream = request.files[f].stream

            # determine all children
            jobs = g.db.execute_many_dict('''
                SELECT cluster_name, dependencies
                FROM job
                WHERE build_id = (SELECT build_id FROM job WHERE id = %s)
                AND state = 'queued'
            ''', [job_id])

            current_cluster = g.db.execute_one_dict('''
                SELECT cluster_name
                FROM job
                WHERE id = %s
            ''', [job_id])['cluster_name']

            clusters = set()

            for j in jobs:
                dependencies = j.get('dependencies', None)

                if not dependencies:
                    continue

                for dep in dependencies:
                    if dep['job-id'] != job_id:
                        continue

                    clusters.add(j['cluster_name'])

            clusters = g.db.execute_many_dict('''
                SELECT root_url
                FROM cluster
                WHERE active = true
                AND enabled = true
                AND name = ANY (%s)
                AND name != %s
                AND name != %s
            ''', [list(clusters), os.environ['INFRABOX_CLUSTER_NAME'], current_cluster])

            g.release_db()

            if not storage.exists(key):
                storage.upload_output(stream, key)

            for c in clusters:
                stream.seek(0)
                url = '%s/api/job/output' % c['root_url']
                files = {f: stream}
                token = encode_job_token(job_id)
                headers = {'Authorization': 'bearer ' + token}
                r = requests.post(url, files=files, headers=headers, timeout=120, verify=False)

                if r.status_code != 200:
                    app.logger.error(r.text)
                    abort(500, "Failed to upload data")

            return jsonify({})

@api.route("/api/job/output/<parent_job_id>", doc=False)
class OutputParent(Resource):

    def get(self, parent_job_id):
        job_id = g.token['job']['id']

        if not validate_uuid(parent_job_id):
            abort(400, "Invalid uuid")

        filename = request.args.get('filename', None)

        if not filename:
            abort(400, "Invalid filename")

        dependencies = g.db.execute_one('''
            SELECT dependencies
            FROM job
            WHERE id = %s
        ''', [job_id])[0]

        is_valid_dependency = False
        for dep in dependencies:
            if dep['job-id'] == parent_job_id:
                is_valid_dependency = True
                break

        if not is_valid_dependency:
            abort(404, "Job not found")

        key = "%s/%s" % (parent_job_id, filename)

        g.release_db()
        f = storage.download_output(key)

        if f:
            return send_file(f)

        c = g.db.execute_one_dict('''
            SELECT *
            FROM cluster
            WHERE name= (
                SELECT cluster_name
                FROM job
                where id = %s)
            ''', [parent_job_id])

        if not c or not c['active'] or not c['enabled']:
            abort(404)
        if c['name'] == os.environ['INFRABOX_CLUSTER_NAME']:
            abort(404)

        token = encode_job_token(job_id)
        headers = {'Authorization': 'bearer ' + token}
        url = '%s/api/job/output/%s' % (c['root_url'], parent_job_id)

        try:
            r = requests.get(url, headers=headers, timeout=120, verify=False)
            f = BytesIO(r.content)
            f.seek(0)
        except:
            f = None
        if not f:
            abort(404)

        return send_file(f)

def find_leaf_jobs(jobs):
    parent_jobs = {}
    leaf_jobs = []

    for j in jobs:
        for d in j.get('depends_on', []):
            parent_jobs[d['job']] = True

    for j in jobs:
        if not parent_jobs.get(j['name'], False):
            leaf_jobs.append(j)

    return leaf_jobs

@api.route("/api/job/create_jobs", doc=False)
class CreateJobs(Resource):
    def get_target_cluster(self, clusters, cluster_selector):
        for c in clusters:
            matches = True
            for s in cluster_selector:
                if s not in c['labels']:
                    matches = False
                    break

            if matches:
                return c['name']

        return None

    def assign_cluster(self, jobs):
        clusters = g.db.execute_many_dict('''
            SELECT name, labels
            FROM cluster
            WHERE active = true
            AND enabled = true
        ''')

        # Shuffle so we can assign the default clusters randomly
        random.shuffle(clusters)

        assigned_clusters = {}

        for j in jobs:
            if 'cluster' not in j:
                j['cluster'] = {}

            cluster_selector = j['cluster'].get('selector', None)
            target_cluster = None

            if not cluster_selector:
                # use the parent cluster
                for d in j.get('depends_on', []):
                    target_cluster = assigned_clusters.get(d['job'], None)
                    break

                if not target_cluster:
                    # use any cluster with label default
                    cluster_selector = ['default']

            if not target_cluster:
                # find a cluster with the selector
                target_cluster = self.get_target_cluster(clusters, cluster_selector)

            if not target_cluster:
                abort(400, 'Could not find a cluster which could satisfy the selector: %s' %
                      json.dumps(cluster_selector))

            assigned_clusters[j['name']] = target_cluster
            j['cluster']['name'] = target_cluster

    def post(self):
        project_id = g.token['project']['id']
        parent_job_id = g.token['job']['id']

        d = request.json
        jobs = d['jobs']

        if not jobs:
            return "No jobs"

        result = g.db.execute_one("SELECT env_var, build_id FROM job WHERE id = %s", [parent_job_id])
        base_env_var = result[0]
        build_id = result[1]

        # Get some project info
        result = g.db.execute_one("""
            SELECT co.user_id, b.build_number, j.project_id FROM collaborator co
            INNER JOIN job j
                ON j.project_id = co.project_id
                AND co.role = 'Owner'
                AND j.id = %s
            INNER JOIN build b
                ON b.id = j.build_id
        """, [parent_job_id])

        build_number = result[1]
        project_id = result[2]

        # name->id mapping
        jobname_id = {}
        for job in jobs:
            name = job["name"]
            job_id = job['id']
            jobname_id[name] = job_id

        for job in jobs:
            job['env_var_refs'] = None
            job['env_vars'] = copy.deepcopy(base_env_var)

            if job['type'] == "wait":
                continue

            avg_duration = g.db.execute_one("""
                SELECT EXTRACT(EPOCH FROM avg(j.end_date - j.start_date))
                FROM job j
                INNER JOIN build b
                    ON b.id = j.build_id
                    AND j.project_id = %s
                    AND b.project_id = %s
                    AND b.build_number between %s and %s
                    AND j.name = %s
                    AND j.state = 'finished'
            """, [project_id, project_id, build_number - 10, build_number, job['name']])[0]

            job['avg_duration'] = avg_duration

            # Handle environment vars
            if 'environment' in job:
                for ename in job['environment']:
                    value = job['environment'][ename]

                    if isinstance(value, dict):
                        env_var_ref_name = value['$secret']
                        result = g.db.execute_many("""
                                    SELECT value FROM secret WHERE name = %s and project_id = %s
                                    """, [env_var_ref_name, project_id])

                        if not result:
                            abort(400, "Secret '%s' not found" % env_var_ref_name)

                        if not job['env_var_refs']:
                            job['env_var_refs'] = {}

                        job['env_var_refs'][ename] = env_var_ref_name
                    else:
                        if not job['env_vars']:
                            job['env_vars'] = {}

                        job['env_vars'][ename] = value

        jobs.sort(key=lambda k: k.get('avg_duration', 0), reverse=True)

        if g.token['job']['name'] != 'Create Jobs':
            # Update names, prefix with parent names
            for j in jobs:
                j['name'] = g.token['job']['name'] + '/' + j['name']

            leaf_jobs = find_leaf_jobs(jobs)

            for j in leaf_jobs:
                wait_job = {
                    'job': j['name'],
                    'job-id': j['id'],
                    'on': ['finished']
                }

                # Update direct children of this job to now wait for the leaf jobs
                g.db.execute('''
                    UPDATE job
                    SET dependencies = dependencies || %s::jsonb
                    WHERE id IN (
                        SELECT id parent_id
                        FROM job, jsonb_array_elements(job.dependencies) as deps
                        WHERE (deps->>'job-id')::uuid = %s
                            AND build_id = %s
                            AND project_id = %s
                    )
                ''', [json.dumps(wait_job), parent_job_id, build_id, project_id])

        self.assign_cluster(jobs)

        for job in jobs:
            name = job["name"]

            job_type = job["type"]
            job_id = job['id']

            depends_on = job.get("depends_on", [])

            if depends_on:
                for dep in depends_on:
                    dep['job-id'] = jobname_id[dep['job']]
            else:
                depends_on = [{"job": g.token['job']['name'], "job-id": parent_job_id, "on": ["finished"]}]

            if job_type == "docker":
                f = job['docker_file']
                t = 'run_project_container'
            elif job_type == "docker-image":
                f = None
                t = 'run_project_container'
            elif job_type == "docker-compose":
                f = job['docker_compose_file']
                t = 'run_docker_compose'
            elif job_type == "wait":
                f = None
                t = 'wait'
            else:
                abort(400, "Unknown job type: %s" % job_type)

            # Create external git repo if necessary
            repo = job.get('repo', None)
            if repo:
                repo = json.dumps(repo)

            # Handle build arguments
            build_arguments = None
            if 'build_arguments' in job:
                build_arguments = json.dumps(job['build_arguments'])

            # Handle Deployments
            deployments = None
            if 'deployments' in job:
                deployments = json.dumps(job['deployments'])

            # Handle env vars
            env_vars = None
            if 'env_vars' in job:
                env_vars = json.dumps(job['env_vars'])

            # Handle env var refs
            env_var_refs = None
            if 'env_var_refs' in job:
                env_var_refs = json.dumps(job['env_var_refs'])

            if 'services' in job:
                for s in job['services']:
                    if 'labels' not in s['metadata']:
                        s['metadata']['labels'] = {}

            # Create job
            g.db.execute("""
                         INSERT INTO job (id, state, build_id, type, dockerfile, name,
                             project_id, dependencies,
                             created_at, repo,
                             env_var_ref, env_var, build_arg, deployment,
                             definition, cluster_name)
                         VALUES (%s, 'queued', %s, %s, %s, %s, %s, %s, %s, %s,
                                 %s, %s, %s, %s, %s, %s);
                         """, [job_id, build_id, t, f, name,
                               project_id,
                               json.dumps(depends_on), datetime.now(),
                               repo, env_var_refs, env_vars,
                               build_arguments, deployments,
                               json.dumps(job), job['cluster']['name']])

        g.db.commit()
        return "Successfully create jobs"

@api.route("/api/job/stats", doc=False)
class Stats(Resource):

    def post(self):
        job_id = g.token['job']['id']

        stats = request.json['stats']
        s = 0
        c = 0
        for _, values in stats.items():
            for v in values:
                c += 1
                s += v['cpu']

        avg_cpu = None

        if c:
            avg_cpu = round(s/c/100, 2)

        try:
            g.db.execute("UPDATE job SET stats = %s, avg_cpu = %s WHERE id = %s", [json.dumps(stats), avg_cpu, job_id])
            g.db.commit()
        except:
            pass

        return jsonify({})


def insert(c, cols, rows, table):
    cursor = c.cursor()
    cols_str = ','.join(cols)

    arg_str = ""
    for r in rows:
        arg_str += "("
        arg_str += ','.join(cursor.mogrify("%s", (x, )) for x in r)
        arg_str += "),"

    arg_str = arg_str[:-1]
    stmt = "INSERT INTO \"%s\" (%s) VALUES %s" % (table, cols_str, arg_str)
    cursor.execute(stmt)
    cursor.close()

@api.route("/api/job/markup", doc=False)
class Markup(Resource):

    def post(self):
        job_id = g.token['job']['id']
        project_id = g.token['project']['id']

        r = g.db.execute_one("""
            SELECT count(*) FROM job_markup WHERE job_id = %s
        """, [job_id])

        if r[0] > 0:
            abort(403, "Forbidden")

        if len(request.files) > 10:
            abort(400, "Too many uploads")

        path = '/tmp/%s.json' % uuid.uuid4()

        @after_this_request
        def _remove_file(response):
            delete_file(path)
            return response

        for name, f in request.files.iteritems():
            try:
                if not allowed_file(f.filename, ("json",)):
                    abort(400, "Filetype not allowed")

                f.save(path)

                # Check size
                if os.path.getsize(path) > 8 * 1024 * 1024:
                    abort(400, "File too big")

                # Parse it
                with open(path, 'r') as md:
                    content = md.read()
                    data = json.loads(content)
                    validate_markup(data)

                g.db.execute("""INSERT INTO job_markup (job_id, name, data, project_id, type)
                                VALUES (%s, %s, %s, %s, 'markup')
                             """, [job_id, name, content, project_id])
                g.db.commit()
            except ValidationError as e:
                abort(400, e.message)
            except Exception as e:
                app.logger.error(e)
                abort(400, "Failed to parse json")

        return jsonify({})

@api.route("/api/job/badge", doc=False)
class Badge(Resource):

    def post(self):
        job_id = g.token['job']['id']
        project_id = g.token['project']['id']

        r = g.db.execute_one(""" SELECT count(*) FROM job_badge WHERE job_id = %s
                             """, [job_id])

        if r[0] > 0:
            abort(403, "Forbidden")

        if len(request.files) > 10:
            abort(400, "Too many uploads")

        path = '/tmp/%s.json' % uuid.uuid4()

        @after_this_request
        def _remove_file(response):
            delete_file(path)
            return response

        for _, f in request.files.iteritems():
            if not allowed_file(f.filename, ("json")):
                abort(400, "Filetype not allowed")

            f.save(path)

            # check file size
            if os.path.getsize(path) > 4 * 1024:
                abort(400, "File too big")

            # Parse it
            try:
                with open(path, 'r') as md:
                    data = json.load(md)
                    validate_badge(data)
            except ValidationError as e:
                abort(400, e.message)
            except:
                abort(400, "Failed to parse json")

            subject = data['subject']
            status = data['status']
            color = data['color']

            g.db.execute("""INSERT INTO job_badge (job_id, subject, status, color, project_id)
                            VALUES (%s, %s, %s, %s, %s)
                         """, [job_id, subject, status, color, project_id])
            g.db.commit()

        return jsonify({})

@api.route("/api/job/testresult", doc=False)
class Testresult(Resource):

    def post(self):
        job_id = g.token['job']['id']
        project_id = g.token['project']['id']

        if 'data' not in request.files:
            abort(400, 'data not set')

        f = request.files['data']

        if not allowed_file(f.filename, ("json")):
            abort(400, 'file ending not allowed')

        path = '/tmp/%s.json' % uuid.uuid4()

        @after_this_request
        def _remove_file(response):
            delete_file(path)
            return response

        f.save(path)

        # check size
        if os.path.getsize(path) > 16 * 1024 * 1024:
            abort(400, "File too big")

        # Parse it
        try:
            with open(path, 'r') as testresult:
                data = json.load(testresult)
        except:
            abort(400, 'Failed to parse json')

        # Validate it
        try:
            validate_result(data)
        except ValidationError as e:
            abort(400, e.message)

        rows = g.db.execute_one("""
            SELECT j.project_id
            FROM job  j
            INNER JOIN build b
                ON j.id = %s
                AND b.id = j.build_id
        """, [job_id])
        project_id = rows[0]

        # Lookup all IDs and prepare insert for missing tests
        test_runs = []
        measurements = []

        tests = data['tests']
        for t in tests:
            if len(t['suite']) > 250:
                t['suite'] = t['suite'][0:250]

            if len(t['name']) > 250:
                t['name'] = t['name'][0:250]

            # Track stats
            if t['status'] == 'fail' or t['status'] == 'failure':
                t['status'] = 'failure'

            # Create the corresponding test run
            test_run_id = str(uuid.uuid4())
            test_runs.append((
                test_run_id,
                t['status'],
                job_id,
                t['duration'],
                project_id,
                t.get('message', None),
                t.get('stack', None),
                t['name'],
                t['suite']
            ))

            # create measurements
            for m in t.get('measurements', []):
                measurements.append((
                    test_run_id,
                    m['name'],
                    m['unit'],
                    m['value'],
                    project_id
                ))

        if measurements:
            insert(g.db.conn, ("test_run_id", "name", "unit", "value", "project_id"), measurements, 'measurement')

        insert(g.db.conn, ("id", "state", "job_id", "duration",
                           "project_id", "message", "stack", "name", "suite"), test_runs, 'test_run')

        g.db.commit()
        return jsonify({})
