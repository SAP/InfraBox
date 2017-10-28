# pylint: disable=too-many-lines,global-statement,too-many-locals,too-many-branches,too-many-statements
from __future__ import print_function
import os
import json
import time
import subprocess
import uuid
import copy
from datetime import datetime

from minio import Minio
import jwt

from flask import Flask, jsonify, request, send_file

from pyinfrabox.badge import validate_badge
from pyinfrabox.markup import validate_markup
from pyinfrabox.testresult import validate_result
from pyinfrabox import ValidationError

from pyinfraboxutils import get_logger, get_env
from pyinfraboxutils.db import connect_db

logger = get_logger('job-api')

app = Flask(__name__)


def execute_many(stmt, args):
    c = conn.cursor()
    c.execute(stmt, args)
    r = c.fetchall()
    c.close()

    return r

def execute_one(stmt, args):
    r = execute_many(stmt, args)

    if not r:
        return r

    return r[0]

def allowed_file(filename, extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions

def validate_token():
    conn.rollback()
    token = request.headers.get('X-Infrabox-Token', None)

    if not token:
        logger.debug('No token header')
        return None

    decoded = None
    try:
        decoded = jwt.decode(token, get_env('INFRABOX_JOB_API_SECRET'))
    except:
        logger.debug('failed to decode token')
        return None

    job_id = decoded['job_id']

    if not validate_uuid4(job_id):
        logger.warn('not a valid uuid')
        return None

    cur = conn.cursor()
    cur.execute("SELECT state, project_id, name FROM job WHERE id = %s", [job_id])
    r = cur.fetchone()
    cur.close()

    if not r:
        logger.debug('job not found')
        return None

    job_state = r[0]
    if job_state not in ('queued', 'running', 'scheduled'):
        logger.warn('job in wrong state')
        return None

    return {
        "job": {
            "id": job_id,
            "state": r[0],
            "name": r[2]
        },
        "project": {
            "id": r[1]
        }
    }

def get_minio_client():
    return Minio(get_env('INFRABOX_STORAGE_S3_ENDPOINT') +
                 ":" + get_env('INFRABOX_STORAGE_S3_PORT'),
                 access_key=get_env('INFRABOX_STORAGE_S3_ACCESS_KEY'),
                 secret_key=get_env('INFRABOX_STORAGE_S3_SECRET_KEY'),
                 secure=get_env('INFRABOX_STORAGE_S3_SECURE') == 'true')


def validate_uuid4(uuid_string):
    try:
        val = uuid.UUID(uuid_string, version=4)
    except ValueError:
        return False

    return val.hex == uuid_string.replace('-', '')

def use_gcs():
    return get_env('INFRABOX_STORAGE_GCS_ENABLED') == 'true'

def use_s3():
    return get_env('INFRABOX_STORAGE_S3_ENABLED') == 'true'

def execute(command):
    process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, universal_newlines=True,
                               env={"PATH": os.environ['PATH']})

    output = ""
    # Poll process for new output until finished
    while True:
        line = process.stdout.readline()
        if not line:
            break

        output += line

    process.wait()

    exitCode = process.returncode
    if exitCode != 0:
        raise Exception(output)


def get_job_data(job_id):
    data = {}

    # get all the job details
    cursor = conn.cursor()
    cursor.execute('''
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
	    j.build_only,
	    j.type,
	    null,
	    j.keep,
	    j.repo,
	    j.base_path,
            j.state,
            j.scan_container,
            j.env_var,
            j.env_var_ref,
            j.cpu,
            j.memory,
            u.id,
            j.build_arg,
            j.deployment,
            j.security_context
	FROM job j
	INNER JOIN build b
	    ON j.build_id = b.id
	    AND j.project_id = b.project_id
	INNER JOIN collaborator co
	    ON co.project_id = j.project_id
	    AND co.owner = true
	INNER JOIN "user" u
	    ON co.user_id = u.id
	INNER JOIN project p
	    ON co.project_id = p.id
	WHERE j.id = %s
    ''', (job_id, ))
    r = cursor.fetchone()
    cursor.close()

    data['job'] = {
        "id": job_id,
        "name": r[0],
        "dockerfile": r[2],
        "build_only": r[12],
        "type": r[13],
        "keep": r[15],
        "repo": r[16],
        "base_path": r[17],
        "state": r[18],
        "scan_container": r[19],
        "cpu": r[22],
        "memory": r[23],
        "build_arguments": r[25],
        "security_context": r[27]
    }

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
        "build_number": r[9]
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
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                r.clone_url, r.name, r.private
            FROM repository r
            WHERE r.project_id = %s
        ''', (data['project']['id'],))
        r = cursor.fetchone()
        cursor.close()

        data['repository']['clone_url'] = r[0]
        data['repository']['name'] = r[1]
        data['repository']['private'] = r[2]

        # A regular commit
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                c.branch, c.committer_name, c.tag, c.pull_request_id
            FROM commit c
            WHERE c.id = %s
                AND c.project_id = %s
        ''', (data['build']['commit_id'], data['project']['id']))
        r = cursor.fetchone()
        cursor.close()

        data['commit'] = {
            "id": data['build']['commit_id'],
            "branch": r[0],
            "committer_name": r[1],
            "tag": r[2]
        }
        pull_request_id = r[3]

    if data['project']['type'] == 'upload':
        cursor = conn.cursor()
        cursor.execute('''
	    SELECT filename FROM source_upload
	    WHERE id = %s
	''', (data['build']['source_upload_id'], ))
        r = cursor.fetchone()
        cursor.close()

        data['source_upload'] = {
            "filename": r[0]
        }

    # get dependencies
    cursor = conn.cursor()
    cursor.execute('''
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
    ''', (data['job']['id'], data['job']['id']))
    r = cursor.fetchall()
    cursor.close()

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
    cursor = conn.cursor()
    cursor.execute('''
      SELECT id, name FROM job where id
          IN (SELECT (deps->>'job-id')::uuid FROM job, jsonb_array_elements(job.dependencies) as deps WHERE id = %s)
    ''', (data['job']['id'], ))
    r = cursor.fetchall()
    cursor.close()

    data['parents'] = []

    for d in r:
        data['parents'].append({
            "id": d[0],
            "name": d[1]
        })

    # get the secrets
    cursor = conn.cursor()
    cursor.execute('''
         SELECT name, value
         FROM secret
         WHERE project_id = %s
    ''', (data['project']['id'], ))
    secrets = cursor.fetchall()
    cursor.close()

    def get_secret(name):
        for ev in secrets:
            if ev[0] == name:
                return ev[1]
        return None

    # Deployments
    data['deployments'] = []
    if deployments:
        for dep in deployments:
            if dep['type'] == 'docker-registry':
                if 'password' not in dep:
                    data['deployments'].append(dep)
                    continue

                secret_name = dep['password']['$ref']
                secret = get_secret(secret_name)

                if not secret:
                    return "Secret %s not found" % secret_name

                dep['password'] = secret
                data['deployments'].append(dep)
            else:
                return "Unknown deployment type", 400

    # Default env vars
    data['environment'] = {
        "TERM": "xterm-256color",
        "INFRABOX_JOB_ID": data['job']['id'],
        "INFRABOX_BUILD_NUMBER": "%s" % data['build']['build_number']
    }

    if data['commit']['branch']:
        data['environment']['INFRABOX_GIT_BRANCH'] = data['commit']['branch']

    if data['commit']['tag']:
        data['environment']['INFRABOX_GIT_TAG'] = data['commit']['tag']

    if pull_request_id:
        data['environment']['INFRABOX_GITHUB_PULL_REQUEST'] = "true"

    if env_vars:
        for name, value in env_vars.iteritems():
            data['environment'][name] = value

    if env_var_refs:
        for name, value in env_var_refs.iteritems():
            secret = get_secret(value)

            if not secret:
                return "Secret %s not found" % value

            data['environment'][name] = secret

    return data

@app.route("/source")
def get_source():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']

    r = execute_one('''
        SELECT su.filename
        FROM
            source_upload su
        INNER JOIN job j
            ON j.source_upload_id = su.id
        WHERE
            j.id = %s
    ''', (job_id,))

    source_zip = '/tmp/source.zip'
    filename = r[0]

    if use_gcs():
        bucket = os.environ['INFRABOX_STORAGE_GCS_PROJECT_UPLOAD_BUCKET']
        execute(('gcloud', 'auth', 'activate-service-account',
                 '--key-file', '/etc/infrabox/gcs/gcs_service_account.json'))

        execute(('gsutil', 'cp',
                 'gs://%s/%s' % (bucket, filename),
                 source_zip))
    else:
        assert use_s3()
        try:
            bucket = os.environ['INFRABOX_STORAGE_S3_PROJECT_UPLOAD_BUCKET']
            mc = get_minio_client()
            mc.fget_object(bucket, filename, source_zip)
        except Exception as e:
            app.logger.error(e)
            raise e

    return send_file(source_zip)

@app.route("/cache", methods=['GET', 'POST'])
def get_cache():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    project_id = token['project']['id']
    job_name = token['job']['name']

    path = '/tmp/cache.tar.gz'
    template = 'project_%s__job_%s.tar.gz'
    cache_identifier = template % (project_id,
                                   job_name)

    if request.method == 'POST':
        if 'data' not in request.files:
            return "No file", 400

        f = request.files['data']
        if not allowed_file(f.filename, ("gz",)):
            return "Filetype not allowed", 400

        f.save(path)

        if os.path.getsize(path) > 100 * 1024 * 1024:
            return "File too big", 400

        if use_gcs():
            execute(('gcloud', 'auth', 'activate-service-account',
                     '--key-file', '/etc/infrabox/gcs/gcs_service_account.json'))

            bucket = os.environ['INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET']
            key = 'gs://%s/%s' % (bucket, cache_identifier)
            execute(('gsutil', 'cp', path, key))
        else:
            assert use_s3()
            bucket = os.environ['INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET']
            mc = get_minio_client()
            mc.fput_object(bucket, cache_identifier, path)

        return "OK"
    elif request.method == 'GET':
        if use_gcs():
            execute(('gcloud', 'auth', 'activate-service-account',
                     '--key-file', '/etc/infrabox/gcs/gcs_service_account.json'))

            bucket = os.environ['INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET']
            key = 'gs://%s/%s' % (bucket, cache_identifier)

            try:
                execute(('gsutil', 'stat', key))
            except:
                return "Not found", 404

            execute(('gsutil', 'cp', key, path))
        else:
            assert use_s3()
            try:
                bucket = os.environ['INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET']
                mc = get_minio_client()
                mc.fget_object(bucket, cache_identifier, path)
            except:
                return "Not found", 404

        return send_file(path)
    else:
        return "Not found", 404

@app.route('/output', methods=['POST'])
def upload_output():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']

    if 'data' not in request.files:
        return "No file", 400

    f = request.files['data']
    if not allowed_file(f.filename, ("gz",)):
        return "Filetype not allowed", 400

    path = '/tmp/output.tar.gz'
    f.save(path)

    max_output_size = os.environ['INFRABOX_JOB_MAX_OUTPUT_SIZE']
    if os.path.getsize(path) > max_output_size:
        return "File too big", 400

    object_name = "%s-%s.tar.gz" % (job_id, str(uuid.uuid4()))

    if use_gcs():
        bucket = os.environ['INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET']
        execute(('gcloud', 'auth', 'activate-service-account',
                 '--key-file', '/etc/infrabox/gcs/gcs_service_account.json'))

        execute(('gsutil', 'cp',
                 path, 'gs://%s/%s' % (bucket, object_name)))
    else:
        assert use_s3()
        bucket = os.environ['INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET']
        mc = get_minio_client()
        mc.fput_object(bucket, object_name, path)

    return "OK"

@app.route("/output/<job_id>")
def get_output_of_job(job_id):
    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']

    if not validate_uuid4(job_id):
        return "Invalid uuid", 400

    dependencies = execute_one('''
        SELECT dependencies
        FROM job
        WHERE id = %s
    ''', (job_id,))[0]

    is_valid_dependency = False
    for dep in dependencies:
        if dep['job-id'] == job_id:
            is_valid_dependency = True
            break

    if not is_valid_dependency:
        return "Job not found", 404

    cursor = conn.cursor()
    cursor.execute('''
        SELECT download FROM job WHERE id = %s
    ''', (job_id, ))
    r = cursor.fetchall()
    cursor.close()

    if len(r) != 1:
        return "Job not found 2: %s" % r, 500

    if not r[0][0]:
        return "Job not found 3: %s" % r, 404

    if 'Output' not in r[0][0]:
        return "Job not found 4: %s" % r[0], 500

    output = r[0][0]["Output"]

    if len(output) != 1:
        return "Job not found 5: %s" % r, 500

    object_name = output[0]['id']
    output_zip = os.path.join('/tmp', job_id + '.tar.gz')

    if use_gcs():
        bucket = os.environ['INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET']
        execute(('gcloud', 'auth', 'activate-service-account',
                 '--key-file', '/etc/infrabox/gcs/gcs_service_account.json'))

        key = 'gs://%s/%s' % (bucket, object_name)
        try:
            execute(('gsutil', 'stat', key))
        except:
            return "Not found", 404

        execute(('gsutil', 'cp', key, output_zip))
    else:
        assert use_s3()
        try:
            bucket = os.environ['INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET']
            mc = get_minio_client()
            mc.fget_object(bucket, object_name, output_zip)
        except:
            return "Not found", 404

    return send_file(output_zip)

@app.route("/job")
def get_job():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']
    job_data = get_job_data(job_id)

    state = job_data['job']['state']
    if state in ("finished", "error", "failure", "skipped", "killed"):
        return jsonify({}), 404

    return jsonify(job_data)

@app.route("/")
def ping():
    return "ok"

@app.route("/setrunning", methods=['POST'])
def set_running():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']

    cursor = conn.cursor()
    cursor.execute("DELETE FROM console WHERE job_id = %s", (job_id,))
    cursor.execute("""UPDATE job SET state = 'running', start_date = current_timestamp
                      WHERE id = %s""", (job_id,))
    cursor.close()
    conn.commit()

    return jsonify({})

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


@app.route("/create_jobs", methods=['POST'])
def create_jobs():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    project_id = token['project']['id']
    parent_job_id = token['job']['id']

    d = request.json
    jobs = d['jobs']

    # Check if capabilities are set and allowed
    if get_env('INFRABOX_JOB_SECURITY_CONTEXT_CAPABILITIES_ENABLED') != 'true':
        for job in jobs:
            sc = job.get('security_context', None)
            if not sc:
                continue

            if sc.get('capabilities', None):
                return 'Capabilities are disabled', 404

    c = conn
    cursor = c.cursor()
    cursor.execute("SELECT env_var, build_id FROM job WHERE id = %s", (parent_job_id,))
    result = cursor.fetchone()
    base_env_var = result[0]
    build_id = result[1]

    # Get some project info
    cursor = c.cursor()
    cursor.execute("""
        SELECT co.user_id, b.build_number, j.project_id FROM collaborator co
        INNER JOIN job j
            ON j.project_id = co.project_id
            AND co.owner = true
            AND j.id = %s
        INNER JOIN build b
            ON b.id = j.build_id
    """, (parent_job_id,))
    result = cursor.fetchone()
    cursor.close()

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

        cursor = c.cursor()
        cursor.execute("""
            SELECT EXTRACT(EPOCH FROM avg(j.end_date - j.start_date))
            FROM job j
            INNER JOIN build b
                ON b.id = j.build_id
                AND j.project_id = %s
                AND b.project_id = %s
                AND b.build_number between %s and %s
                AND j.name = %s
                AND j.state = 'finished'
        """, (project_id, project_id, build_number - 10, build_number, job['name'],))
        avg_duration = cursor.fetchone()[0]
        cursor.close()

        job['avg_duration'] = avg_duration

        # Handle environment vars
        if 'environment' in job:
            for ename in job['environment']:
                value = job['environment'][ename]

                if isinstance(value, dict):
                    env_var_ref_name = value['$ref']
                    cursor = c.cursor()
                    cursor.execute("""SELECT value FROM secret WHERE name = %s and project_id = %s""",
                                   (env_var_ref_name, project_id))
                    result = cursor.fetchall()
                    cursor.close()

                    if not result:
                        return "Environment variable '%s' not found in project" % env_var_ref_name, 400

                    if not job['env_var_refs']:
                        job['env_var_refs'] = {}

                    job['env_var_refs'][ename] = env_var_ref_name
                else:
                    if not job['env_vars']:
                        job['env_vars'] = {}

                    job['env_vars'][ename] = value

    jobs.sort(key=lambda k: k.get('avg_duration', 0), reverse=True)

    if token['job']['name'] != 'Create Jobs':
        # Update names, prefix with parent names
        for j in jobs:
            j['name'] = token['job']['name'] + '/' + j['name']

        leaf_jobs = find_leaf_jobs(jobs)

        for j in leaf_jobs:
            wait_job = {
                'job': j['name'],
                'job-id': j['id'],
                'on': ['finished']
            }

            # Update direct children of this job to now wait for the leaf jobs
            cursor = c.cursor()
            cursor.execute('''
                UPDATE job
                SET dependencies = dependencies || %s::jsonb
                WHERE id IN (
                    SELECT id parent_id
                    FROM job, jsonb_array_elements(job.dependencies) as deps
                    WHERE (deps->>'job-id')::uuid = %s
                    AND build_id = %s
                    AND project_id = %s
                )
            ''', (json.dumps(wait_job), job_id, build_id, project_id))
            cursor.close()

    for job in jobs:
        name = job["name"]

        job_type = job["type"]
        job_id = job['id']

        build_only = job.get("build_only", True)
        keep = job.get("keep", False)
        scan_container = False

        if 'security' in job:
            scan_container = job['security']['scan_container']

        depends_on = job.get("depends_on", [])

        if depends_on:
            for dep in depends_on:
                dep['job-id'] = jobname_id[dep['job']]
        else:
            depends_on = [{"job": token['job']['name'], "job-id": parent_job_id, "on": ["finished"]}]

        if job_type == "docker":
            f = job['docker_file']
            t = 'run_project_container'
        elif job_type == "docker-compose":
            f = job['docker_compose_file']
            t = 'run_docker_compose'
        elif job_type == "wait":
            f = None
            t = 'wait'
        else:
            return "Unknown job type", 400

        limits_cpu = 1
        limits_memory = 1024
        timeout = job.get('timeout', 3600)

        if 'resources' in job and 'limits' in job['resources']:
            limits_cpu = job['resources']['limits']['cpu']
            limits_memory = job['resources']['limits']['memory']

        # Create external git repo if necessary
        if job.get('repo', None):
            repo = json.dumps(job['repo'])
        else:
            repo = None

        base_path = job.get('base_path', None)
        if base_path == '':
            base_path = None

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

        # Handle resources
        resources = None
        if 'resources' in job:
            resources = json.dumps(job['resources'])

        # Create job
        cursor = c.cursor()
        cursor.execute("""
            INSERT INTO job (id, state, build_id, type, dockerfile, name,
                project_id, dependencies, build_only,
                keep, created_at, repo, base_path, scan_container,
                env_var_ref, env_var, build_arg, deployment, cpu, memory, timeout, resources)
            VALUES (%s, 'queued', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                       (job_id, build_id, t, f, name,
                        project_id,
                        json.dumps(depends_on), build_only, keep, datetime.now(),
                        repo, base_path, scan_container, env_var_refs, env_vars,
                        build_arguments, deployments, limits_cpu, limits_memory, timeout,
                        resources))
        cursor.close()

        # to make sure the get picked up in the right order by the scheduler
        time.sleep(0.1)

    c.commit()
    return "Successfully create jobs"

@app.route("/consoleupdate", methods=['POST'])
def post_console():
    output = request.json['output']

    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']

    r = execute_one("""
        SELECT sum(char_length(output)), count(*) FROM console WHERE job_id = %s
    """, (job_id,))

    if not r:
        return "Not found", 404

    console_output_len = r[0]
    console_output_updates = r[1]

    if console_output_len > 16 * 1024 * 1024:
        return "Console output too big", 400

    if console_output_updates > 4000:
        return "Too many console updates", 400

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO console (job_id, output) VALUES (%s, %s)", (job_id, output))
        cursor.close()
        conn.commit()
    except:
        pass

    return jsonify({})

@app.route("/stats", methods=['POST'])
def post_stats():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']

    stats = request.json['stats']

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE job SET stats = %s WHERE id = %s", (json.dumps(stats), job_id))
        cursor.close()
        conn.commit()
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

@app.route('/markdown', methods=['POST'])
def upload_markdown():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']
    project_id = token['project']['id']

    r = execute_one("""
        SELECT count(*) FROM job_markup WHERE job_id = %s
    """, (job_id,))

    if not r:
        return "Not found", 404

    if r[0] > 0:
        return "Forbidden", 403

    if len(request.files) > 10:
        return "Too many uploads", 400

    for name, f in request.files.iteritems():
        if not allowed_file(f.filename, ("md",)):
            return "Filetype not allowed", 400

        path = '/tmp/data.md'
        f.save(path)

        if os.path.getsize(path) > 8 * 1024 * 1024:
            return "File too big", 400

        with open(path, 'r') as md:
            data = md.read()

        cursor = conn.cursor()
        cursor.execute("""INSERT INTO job_markup (job_id, name, data, project_id, type)
                          VALUES (%s, %s, %s, %s, 'markdown')""",
                       (job_id, name, data, project_id))
        cursor.close()
        conn.commit()
        return ""

@app.route('/markup', methods=['POST'])
def upload_markup():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']
    project_id = token['project']['id']

    r = execute_one("""
        SELECT count(*) FROM job_markup WHERE job_id = %s
    """, (job_id,))

    if r[0] > 0:
        return "Forbidden", 403

    if len(request.files) > 10:
        return "Too many uploads", 400

    for name, f in request.files.iteritems():
        try:
            if not allowed_file(f.filename, ("json",)):
                return "Filetype not allowed", 400

            path = '/tmp/data.json'
            f.save(path)

            # Check size
            if os.path.getsize(path) > 8 * 1024 * 1024:
                return "File too big", 400

            # Parse it
            with open(path, 'r') as md:
                content = md.read()
                data = json.loads(content)
                validate_markup(data)

            cursor = conn.cursor()
            cursor.execute("""INSERT INTO job_markup (job_id, name, data, project_id, type)
                              VALUES (%s, %s, %s, %s, 'markup')""",
                           (job_id, name, content, project_id))
            cursor.close()
            conn.commit()
        except ValidationError as e:
            return e.message, 400
        except Exception as e:
            app.logger.error(e)
            return "Failed to parse json", 400

    return ""

@app.route('/badge', methods=['POST'])
def upload_badge():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']
    project_id = token['project']['id']

    r = execute_one("""
        SELECT count(*) FROM job_badge WHERE job_id = %s
    """, (job_id,))

    if r[0] > 0:
        return "Forbidden", 403

    if len(request.files) > 10:
        return "Too many uploads", 400

    for _, f in request.files.iteritems():
        if not allowed_file(f.filename, ("json",)):
            return "Filetype not allowed", 400

        path = '/tmp/data.json'
        f.save(path)

        # check file size
        if os.path.getsize(path) > 4 * 1024:
            return "File too big", 400

        # Parse it
        try:
            with open(path, 'r') as md:
                data = json.load(md)
                validate_badge(data)
        except ValidationError as e:
            return e.message, 400
        except:
            return "Failed to parse json", 400

        subject = data['subject']
        status = data['status']
        color = data['color']

        cursor = conn.cursor()
        cursor.execute("""INSERT INTO job_badge (job_id, subject, status, color, project_id)
                          VALUES (%s, %s, %s, %s, %s)""",
                       (job_id, subject, status, color, project_id))
        cursor.close()
        conn.commit()
        return ""


@app.route('/testresult', methods=['POST'])
def upload_testresult():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']
    project_id = token['project']['id']

    if 'data' not in request.files:
        return jsonify({}), 400

    f = request.files['data']

    if not allowed_file(f.filename, ("json"),):
        return jsonify({}), 400

    path = '/tmp/testresult.json'

    f.save(path)

    # check size
    if os.path.getsize(path) > 16 * 1024 * 1024:
        return "File too big", 400

    # Parse it
    try:
        with open(path, 'r') as testresult:
            data = json.load(testresult)
    except:
        return 'Failed to parse json', 404

    # Validate it
    try:
        validate_result(data)
    except ValidationError as e:
        return e.message, 400

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM test_run WHERE job_id=%s", (job_id,))
    testruns = cursor.fetchone()

    if testruns[0] > 0:
        return "", 404

    cursor = conn.cursor()
    cursor.execute("""SELECT j.project_id, b.build_number
            FROM job  j
            INNER JOIN build b
                ON j.id = %s
                AND b.id = j.build_id
    """, (job_id,))
    rows = cursor.fetchone()
    project_id = rows[0]
    build_number = rows[1]

    cursor = conn.cursor()
    cursor.execute("""SELECT name, suite, id FROM test WHERE project_id = %s""", (project_id,))
    existing_tests = cursor.fetchall()

    test_index = {}
    for t in existing_tests:
        test_index[t[0] + '|' + t[1]] = t[2]

    # Lookup all IDs and prepare insert for missing tests
    missing_tests = []
    test_runs = []
    measurements = []

    stats = {
        "tests_added": 0,
        "tests_duration": 0,
        "tests_skipped": 0,
        "tests_failed": 0,
        "tests_error": 0,
        "tests_passed": 0,
    }

    tests = data['tests']
    for t in tests:
        # check if if already exists
        test_id = None
        if t['suite'] + '|' + t['name'] in test_index:
            # existing test
            test_id = test_index[t['suite'] + '|' + t['name']]
        else:
            # new test
            test_id = str(uuid.uuid4())
            missing_tests.append((
                t['name'],
                t['suite'],
                project_id,
                test_id,
                build_number
            ))

        # Track stats
        if t['status'] == 'fail' or t['status'] == 'failure':
            t['status'] = 'failure'
            stats['tests_failed'] += 1
        elif t['status'] == 'ok':
            stats['tests_passed'] += 1
        elif t['status'] == 'skipped':
            stats['tests_skipped'] += 1
        elif t['status'] == 'error':
            stats['tests_error'] += 1

        stats['tests_duration'] += t['duration']

        # Create the corresponding test run
        test_run_id = str(uuid.uuid4())
        test_runs.append((
            test_run_id,
            t['status'],
            job_id,
            test_id,
            t['duration'],
            project_id,
            t.get('message', None),
            t.get('stack', None)
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

    if missing_tests:
        insert(conn, ("name", "suite", "project_id", "id", "build_number"), missing_tests, 'test')

    if measurements:
        insert(conn, ("test_run_id", "name", "unit", "value", "project_id"), measurements, 'measurement')

    insert(conn, ("id", "state", "job_id", "test_id", "duration",
                  "project_id", "message", "stack"), test_runs, 'test_run')

    insert(conn, ("tests_added", "tests_duration", "tests_skipped", "tests_failed", "tests_error",
                  "tests_passed", "job_id", "project_id"),
           ((stats['tests_added'], stats['tests_duration'], stats['tests_skipped'],
             stats['tests_failed'], stats['tests_error'], stats['tests_passed'],
             job_id, project_id),), 'job_stat')

    conn.commit()
    return "", 200


@app.route("/setfinished", methods=['POST'])
def set_finished():
    token = validate_token()

    if not token:
        return "Forbidden", 403

    job_id = token['job']['id']

    state = request.json['state']
    # collect console output
    cursor = conn.cursor()
    cursor.execute("""SELECT output FROM console WHERE job_id = %s
                      ORDER BY date""", (job_id,))
    lines = cursor.fetchall()

    output = ""
    for l in lines:
        output += l[0]

    # Update state
    cursor.execute("""
    UPDATE job SET
        state = %s,
        console = %s,
        end_date = current_timestamp
    WHERE id = %s""", (state, output, job_id))

    # remove form console table
    cursor.execute("DELETE FROM console WHERE job_id = %s", (job_id,))
    cursor.close()

    conn.commit()
    return jsonify({})

if __name__ == "__main__":
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_JOB_MAX_OUTPUT_SIZE')
    get_env('INFRABOX_JOB_SECURITY_CONTEXT_CAPABILITIES_ENABLED')
    get_env('INFRABOX_JOB_API_SECRET')

    if get_env('INFRABOX_STORAGE_GCS_ENABLED') == 'true':
        get_env('INFRABOX_STORAGE_GCS_CONTAINER_CONTENT_CACHE_BUCKET')
        get_env('INFRABOX_STORAGE_GCS_CONTAINER_OUTPUT_BUCKET')
        get_env('INFRABOX_STORAGE_GCS_PROJECT_UPLOAD_BUCKET')

    if get_env('INFRABOX_STORAGE_S3_ENABLED') == 'true':
        get_env('INFRABOX_STORAGE_S3_CONTAINER_CONTENT_CACHE_BUCKET')
        get_env('INFRABOX_STORAGE_S3_CONTAINER_OUTPUT_BUCKET')
        get_env('INFRABOX_STORAGE_S3_PROJECT_UPLOAD_BUCKET')
        get_env('INFRABOX_STORAGE_S3_REGION')

    conn = connect_db()

    app.run(host="0.0.0.0", debug=True, port=8080)
