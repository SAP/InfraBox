#!/usr/bin/python
import os
import shutil
import json
import subprocess
import logging
import stat
import uuid
import base64
import argparse
import requests
import yaml

from pyinfrabox.infrabox import validate_json
from pyinfrabox.docker_compose import create_from

from infrabox_job.stats import StatsCollector
from infrabox_job.process import ApiConsole, Failure
from infrabox_job.job import Job

from pyinfraboxutils import get_env, print_stackdriver

def makedirs(path):
    os.makedirs(path)
    os.chmod(path, 0o777)

def get_registry_name():
    n = os.environ['INFRABOX_DOCKER_REGISTRY_URL'].replace('https://', '')
    n = n.replace('http://', '')
    return n

class RunJob(Job):
    def __init__(self, console, job_type):
        Job.__init__(self)
        self.console = console
        self.data_dir = '/data/infrabox'
        self.job_type = job_type
        self.storage_dir = '/tmp/storage'

        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

        if os.path.exists(self.storage_dir):
            shutil.rmtree(self.storage_dir)

        os.makedirs(self.storage_dir)

        #
        # /tmp/infrabox is mounted to the same path on the host
        # So we can use it to transfer data between the job and
        # the job.py container.
        #

        # <data_dir>/cache is mounted in the job to /infrabox/cache
        self.infrabox_cache_dir = os.path.join(self.data_dir, 'cache')
        makedirs(self.infrabox_cache_dir)

        # <data_dir>/inputs is mounted in the job to /infrabox/inputs
        self.infrabox_inputs_dir = os.path.join(self.data_dir, 'inputs')
        makedirs(self.infrabox_inputs_dir)

        # <data_dir>/output is mounted in the job to /infrabox/output
        self.infrabox_output_dir = os.path.join(self.data_dir, 'output')
        makedirs(self.infrabox_output_dir)

        # <data_dir>/upload is mounted in the job to /infrabox/upload
        self.infrabox_upload_dir = os.path.join(self.data_dir, 'upload')
        makedirs(self.infrabox_upload_dir)

        # <data_dir>/upload/testresult is mounted in the job to /infrabox/upload/testresult
        self.infrabox_testresult_dir = os.path.join(self.infrabox_upload_dir, 'testresult')
        makedirs(self.infrabox_testresult_dir)

        # <data_dir>/upload/markdown is mounted in the job to /infrabox/upload/markdown
        self.infrabox_markdown_dir = os.path.join(self.infrabox_upload_dir, 'markdown')
        makedirs(self.infrabox_markdown_dir)

        # <data_dir>/upload/markup is mounted in the job to /infrabox/upload/markup
        self.infrabox_markup_dir = os.path.join(self.infrabox_upload_dir, 'markup')
        makedirs(self.infrabox_markup_dir)

        # <data_dir>/upload/badge is mounted in the job to /infrabox/upload/badge
        self.infrabox_badge_dir = os.path.join(self.infrabox_upload_dir, 'badge')
        makedirs(self.infrabox_badge_dir)

    def create_jobs_json(self):
        # create job.json
        infrabox_job_json = os.path.join(self.data_dir, 'job.json')
        with open(infrabox_job_json, 'w') as out:
            o = {
                "parent_jobs": self.dependencies,
                "job": {
                    "id": self.job['id'],
                    "name": self.job['name'],
                },
                "project": {
                    "name": self.project['name'],
                },
                "build": {
                    "id": self.build['id'],
                    "number": self.build['build_number'],
                    "url": os.environ['INFRABOX_DASHBOARD_URL'] \
                           + '/dashboard/project/' + self.project['id'] \
                           + '/build/' + self.build['id']
                }
            }

            if self.project['type'] == 'github':
                o['commit'] = {}
                o['commit']["branch"] = self.commit['branch']
                o['commit']["id"] = self.commit['id']

            json.dump(o, out)

    def create_gosu(self):
        infrabox_gosu = os.path.join(self.data_dir, 'gosu.sh')
        with open(infrabox_gosu, 'w') as out:
            out.write('''#!/bin/sh
exec "$@"
''')
            st = os.stat(infrabox_gosu)
            os.chmod(infrabox_gosu, st.st_mode | stat.S_IEXEC)

    def flush(self):
        self.console.flush()

    def compress(self, source, output, _):
        subprocess.check_call("tar cf - --directory %s . | pigz -n > %s" % (source, output), shell=True)

    def uncompress(self, source, output, c):
        cmd = "pigz -dc %s | tar x -C %s" % (source, output)
        c.collect(cmd, show=True)
        subprocess.check_call(cmd, shell=True)

    def get_files_in_dir(self, d, ending):
        result = []
        for root, _, files in os.walk(d):
            for f in files:
                if not f.endswith(ending):
                    continue

                if len(f) < len(ending):
                    continue

                result.append(os.path.join(root, f))

        return result

    def get_source(self):
        c = self.console

        if self.job['repo']:
            repo = self.job['repo']
            clone_url = repo['clone_url']
            branch = repo.get('branch', None)
            private = repo.get('github_private_repo', False)
            ref = repo.get('ref', None)
            commit = repo['commit']

            if private:
                clone_url = clone_url.replace('github.com',
                                              '%s@github.com' % self.repository['github_api_token'])

            env = [
                "-e", "INFRABOX_CLONE_URL=%s" % clone_url,
                "-e", "INFRABOX_COMMIT=%s" % commit,
                "-e", "INFRABOX_GENERAL_NO_CHECK_CERTIFICATES=%s" % os.environ['INFRABOX_GENERAL_NO_CHECK_CERTIFICATES']
            ]

            gerrit_port = os.environ.get('INFRABOX_GERRIT_PORT', None)
            gerrit_hostname = os.environ.get('INFRABOX_GERRIT_HOSTNAME', None)
            if gerrit_port:
                env += [
                    "-e", "INFRABOX_GERRIT_PORT=%s" % gerrit_port,
                    "-e", "INFRABOX_GERRIT_HOSTNAME=%s" % gerrit_hostname
                ]

            if ref:
                env += ["-e", "INFRABOX_REF=%s" % ref]

            if branch:
                env += ["-e", "INFRABOX_BRANCH=%s" % branch]

            cmd = ['docker', 'build', '-f', 'git/Dockerfile', '-t', 'clone', '.']
            c.execute(cmd, show=True, cwd='/job')

            cmd = ['docker', 'run', '-v', '/repo:/repo']
            cmd += env

            if os.path.exists('/tmp/gerrit/id_rsa'):
                cmd += ['-v', '/tmp/gerrit/id_rsa:/tmp/gerrit/id_rsa']

            cmd += ['clone']

            c.execute(cmd, show=True)
        elif self.project['type'] == 'upload':
            c.header("Downloading Source")
            storage_source_zip = os.path.join(self.storage_dir, 'source.zip')
            self.get_file_from_api_server('/source', storage_source_zip)
            os.makedirs('/repo')
            c.execute(['unzip', storage_source_zip, '-d', '/repo'])
        elif self.project['type'] == 'test':
            pass
        else:
            raise Exception('Unknown project type')


    def main_create_jobs(self):
        c = self.console

        if not os.path.isfile('/repo/infrabox.json'):
            raise Failure("infrabox.json not found")

        c.header("Parsing infrabox.json", show=True)
        data = self.parse_infrabox_json('/repo/infrabox.json')
        self.check_file_exist(data)

        c.header("Creating jobs", show=True)
        jobs = self.get_job_list(data, c, self.job['repo'], infrabox_paths={"/repo/infrabox.json": True})
        self.create_jobs(jobs)
        c.collect("Done creating jobs\n")

    def check_container_crashed(self):
        # if the started file exists already this
        # means the container crashed and restarted.
        # then we just mark it as failed.
        p = os.path.join(self.data_dir, "started")

        if os.path.exists(p):
            raise Failure("Container crashed")
        else:
            with open(p, 'w+') as f:
                f.write("started")

    def main(self):
        self.update_status('running')
        self.get_source()

        if self.job_type == 'create':
            self.main_create_jobs()
        else:
            self.main_run_job()

    def upload_test_results(self):
        c = self.console
        c.header("Uploading test results", show=True)
        if os.path.exists(self.infrabox_testresult_dir):
            files = self.get_files_in_dir(self.infrabox_testresult_dir, ".json")

            for f in files:
                tr_path = os.path.join(self.infrabox_testresult_dir, f)
                c.collect("%s\n" % tr_path, show=True)
                r = requests.post("%s/testresult" % self.api_server,
                                  headers=self.get_headers(),
                                  files={"data": open(tr_path)}, timeout=10)
                c.collect("%s\n" % r.text, show=True)


    def upload_markdown_files(self):
        c = self.console
        c.header("Uploading markdown files", show=False)
        if os.path.exists(self.infrabox_markdown_dir):
            files = self.get_files_in_dir(self.infrabox_markdown_dir, ".md")

            for f in files:
                file_name = os.path.basename(f)
                r = requests.post("%s/markdown" % self.api_server,
                                  headers=self.get_headers(),
                                  files={file_name: open(os.path.join(self.infrabox_markdown_dir, f))}, timeout=10)
                c.collect("%s\n" % r.text, show=False)

    def upload_markup_files(self):
        c = self.console
        c.header("Uploading markup files", show=True)
        if os.path.exists(self.infrabox_markup_dir):
            files = self.get_files_in_dir(self.infrabox_markup_dir, ".json")

            for f in files:
                file_name = os.path.basename(f)
                f = open(os.path.join(self.infrabox_markup_dir, f))
                r = requests.post("%s/markup" % self.api_server,
                                  headers=self.get_headers(),
                                  files={file_name: f}, timeout=10)
                c.collect(f.read(), show=True)
                c.collect("%s\n" % r.text, show=True)

    def upload_badge_files(self):
        c = self.console
        c.header("Uploading badge files", show=True)
        if os.path.exists(self.infrabox_badge_dir):
            files = self.get_files_in_dir(self.infrabox_badge_dir, ".json")

            for f in files:
                file_name = os.path.basename(f)
                r = requests.post("%s/badge" % self.api_server,
                                  headers=self.get_headers(),
                                  files={file_name: open(os.path.join(self.infrabox_badge_dir, f))}, timeout=10)
                c.collect("%s\n" % r.text, show=True)

    def create_dynamic_jobs(self):
        c = self.console
        infrabox_json_path = os.path.join(self.infrabox_output_dir, 'infrabox.json')
        if os.path.exists(infrabox_json_path):
            c.header("Creating jobs", show=True)
            data = self.parse_infrabox_json(infrabox_json_path)
            self.check_file_exist(data)
            jobs = self.get_job_list(data, c, self.job['repo'], infrabox_paths={infrabox_json_path: True})
            self.create_jobs(jobs)

    def main_run_job(self):
        c = self.console
        self.create_jobs_json()
        self.create_gosu()

        # base dir for inputs
        storage_inputs_dir = os.path.join(self.storage_dir, 'inputs')

        # Sync deps
        c.header("Syncing inputs", show=True)
        for dep in self.parents:
            storage_input_file_dir = os.path.join(storage_inputs_dir, dep['id'])
            os.makedirs(storage_input_file_dir)

            storage_input_file_tar = os.path.join(storage_input_file_dir, 'output.tar.gz')
            self.get_file_from_api_server('/output/%s' % dep['id'], storage_input_file_tar)

            if os.path.isfile(storage_input_file_tar):
                c.collect("output found for %s\n" % dep['name'], show=True)
                c.execute(['ls', '-alh', storage_input_file_tar], show=True)
                infrabox_input_dir = os.path.join(self.infrabox_inputs_dir, dep['name'].split('/')[-1])
                os.makedirs(infrabox_input_dir)
                self.uncompress(storage_input_file_tar, infrabox_input_dir, c)
                os.remove(storage_input_file_tar)
            else:
                c.collect("no output found for %s\n" % dep['name'], show=True)

        # <storage_dir>/cache is synced with the corresponding
        # Storage path which stores the compressed cache
        storage_cache_dir = os.path.join(self.storage_dir, 'cache')
        os.makedirs(storage_cache_dir)

        storage_cache_tar = os.path.join(storage_cache_dir, 'cache.tar.gz')

        c.header("Syncing cache", show=True)
        self.get_file_from_api_server("/cache", storage_cache_tar)

        c.header("Unpack cache", show=True)

        if os.path.isfile(storage_cache_tar):
            try:
                c.execute(['time', 'tar', '-zxf', storage_cache_tar, '-C', self.infrabox_cache_dir], show=True)
                c.collect("cache found\n", show=True)
            except:
                c.collect("Failed to unpack cache\n", show=True)
            os.remove(storage_cache_tar)
        else:
            c.collect("no cache found\n", show=True)

        try:
            if self.job['type'] == 'run_project_container':
                self.run_container(c)
            elif self.job['type'] == 'run_docker_compose':
                self.run_docker_compose(c)
            else:
                raise Exception('Unknown job type')
        except:
            raise
        finally:
            self.upload_test_results()
            self.upload_markdown_files()
            self.upload_markup_files()
            self.upload_badge_files()

        self.create_dynamic_jobs()

        # Compressing output
        c.header("Compressing output", show=True)
        if os.path.isdir(self.infrabox_output_dir) and os.listdir(self.infrabox_output_dir):
            storage_output_dir = os.path.join(self.storage_dir, self.job['id'])
            os.makedirs(storage_output_dir)

            storage_output_tar = os.path.join(storage_output_dir, 'output.tar.gz')
            self.compress(self.infrabox_output_dir, storage_output_tar, c)

            max_output_size = os.environ['INFRABOX_JOB_MAX_OUTPUT_SIZE']
            if os.stat(storage_output_tar).st_size > max_output_size:
                raise Failure("Output too large")

            c.header("Saving output", show=True)
            self.post_file_to_api_server("/output", storage_output_tar)
        else:
            c.collect("Output is empty\n", show=True)

        # Compressing cache
        c.header("Compressing cache", show=True)
        if os.path.isdir(self.infrabox_cache_dir) and os.listdir(self.infrabox_cache_dir):
            self.compress(self.infrabox_cache_dir, storage_cache_tar, c)
            c.execute(['md5sum', storage_cache_tar], show=True)

            if os.stat(storage_cache_tar).st_size > (1024 * 1024 * 100):
                # cache too big
                c.collect("Cache is too big, not uploading it\n", show=True)
            else:
                c.header("Syncing cache", show=True)
                try:
                    self.post_file_to_api_server('/cache', storage_cache_tar)
                except:
                    logging.exception("message")
        else:
            c.collect("Cache is empty\n", show=True)

        shutil.rmtree(self.data_dir, True)
        shutil.rmtree(self.infrabox_cache_dir, True)

    def run_docker_compose(self, c):
        c.header("Build containers", show=True)
        f = self.job['dockerfile']

        if self.job.get('base_path', None):
            f = os.path.join(self.job['base_path'], f)

        compose_file = os.path.join('/repo', f)
        compose_file_new = compose_file + ".infrabox"

        # rewrite compose file
        compose_file_content = create_from(compose_file)
        for service in compose_file_content['services']:
            service_cache_dir = os.path.join(self.infrabox_cache_dir, service)

            if not os.path.exists(service_cache_dir):
                makedirs(service_cache_dir)

            service_output_dir = os.path.join(self.infrabox_output_dir, service)
            makedirs(service_output_dir)

            service_testresult_dir = os.path.join(self.infrabox_testresult_dir, service)
            makedirs(service_testresult_dir)

            service_markdown_dir = os.path.join(self.infrabox_markdown_dir, service)
            makedirs(service_markdown_dir)

            service_markup_dir = os.path.join(self.infrabox_markup_dir, service)
            makedirs(service_markup_dir)

            service_badge_dir = os.path.join(self.infrabox_badge_dir, service)
            makedirs(service_badge_dir)

            service_volumes = [
                "/repo:/infrabox/context",
                "%s:/infrabox/cache" % service_cache_dir,
                "%s:/infrabox/inputs" % self.infrabox_inputs_dir,
                "%s:/infrabox/output" % service_output_dir,
                "%s:/infrabox/upload/testresult" % service_testresult_dir,
                "%s:/infrabox/upload/markdown" % service_markdown_dir,
                "%s:/infrabox/upload/markup" % service_markup_dir,
                "%s:/infrabox/upload/badge" % service_badge_dir,
            ]

            if os.environ['INFRABOX_LOCAL_CACHE_ENABLED'] == 'true':
                service_volumes.append("/local-cache:/infrabox/local-cache")

            compose_file_content['services'][service]['volumes'] = service_volumes
        with open(compose_file_new, "w+") as out:
            yaml.dump(compose_file_content, out, default_flow_style=False)

        collector = StatsCollector()

        try:
            self.environment['PATH'] = os.environ['PATH']
            c.execute(['docker-compose', '-f', compose_file_new, 'build'],
                      show=True, env=self.environment)
            c.header("Run docker-compose", show=True)

            cwd = self.job.get('base_path', None)
            if cwd:
                cwd = os.path.join('/repo', cwd)


            c.execute(['docker-compose', '-f', compose_file_new, 'up',
                       '--abort-on-container-exit'], env=self.environment, show=True, cwd=cwd)
            c.execute(['docker-compose', '-f', compose_file_new, 'ps'], env=self.environment, cwd=cwd)
            c.execute(['get_compose_exit_code.sh', compose_file_new], env=self.environment, cwd=cwd)
        except:
            raise Failure("Failed to build and run container")
        finally:
            collector.stop()
            self.post_stats(collector.get_result())

        return True

    def deploy_container(self, image_name):
        c = self.console
        c.header("Deploying", show=True)
        if not self.deployments:
            c.collect("No deployments configured\n", show=True)

        for dep in self.deployments:
            tag = dep.get('tag', 'build_%s' % self.build['build_number'])
            dep_image_name = dep['host'] + '/' + dep['repository'] + ":" + tag
            c.execute(['docker', 'tag', image_name, dep_image_name], show=True)
            c.execute(['docker', 'push', dep_image_name], show=True)

    def push_container(self, image_name):
        c = self.console
        c.header("Uploading to docker registry", show=True)

        try:
            if self.job['build_only']:
                c.collect("Not pushing container, because build_only is set.\n", show=True)
            elif not self.job['keep']:
                c.collect("Not pushing container, because keep is not set.\n", show=True)
            else:
                c.execute(['docker', 'login',
                           '-u', os.environ['INFRABOX_DOCKER_REGISTRY_ADMIN_USERNAME'],
                           '-p', os.environ['INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD'],
                           get_registry_name()], show=False)

                c.execute(['docker', 'push', image_name], show=True)
        except Exception as e:
            raise Failure(e.__str__())

    def run_docker_container(self, image_name):
        if self.job['build_only']:
            return

        c = self.console
        collector = StatsCollector()

        container_name = self.job['id']
        cmd = ['docker', 'run', '--name', container_name, '-v', self.data_dir + ':/infrabox']

        # Mount context
        cmd += ['-v', '/repo:/infrabox/context']

        # Mount docker socket
        if os.environ['INFRABOX_JOB_MOUNT_DOCKER_SOCKET'] == 'true':
            cmd += ['-v', '/var/run/docker.sock:/var/run/docker.sock']

        # Add local cache
        if os.environ['INFRABOX_LOCAL_CACHE_ENABLED'] == 'true':
            cmd += ['-v', "/local-cache:/infrabox/local-cache"]

        # add env vars
        for name, value in self.environment.iteritems():
            cmd += ['-e', '%s=%s' % (name, value)]

        # add resource env vars
        os.makedirs('/tmp/serviceaccount')
        if os.environ.get('INFRABOX_RESOURCES_KUBERNETES_CA_CRT', None):
            with open('/tmp/serviceaccount/ca.crt', 'w') as o:
                o.write(base64.b64decode(os.environ['INFRABOX_RESOURCES_KUBERNETES_CA_CRT']))

            with open('/tmp/serviceaccount/token', 'w') as o:
                o.write(base64.b64decode(os.environ['INFRABOX_RESOURCES_KUBERNETES_TOKEN']))

            with open('/tmp/serviceaccount/namespace', 'w') as o:
                o.write(base64.b64decode(os.environ['INFRABOX_RESOURCES_KUBERNETES_NAMESPACE']))

            cmd += ['-v', '/tmp/serviceaccount:/var/run/secrets/kubernetes.io/serviceaccount']


        # Add capabilities

        security_context = self.job.get('security_context', {})

        if security_context:
            capabilities = security_context.get('capabilities', {})
            add_capabilities = capabilities.get('add', [])
            if add_capabilities:
                cmd += ['--cap-add=%s' % ','.join(add_capabilities)]

        cmd += [image_name]

        try:
            c.header("Run container", show=True)
            c.execute(cmd, show=True)
            c.execute(("docker", "commit", container_name, image_name))
        except:
            try:
                c.execute(("docker", "commit", container_name, image_name))
                self.push_container(image_name)
            except:
                pass

            raise Failure("Container run exited with error")
        finally:
            collector.stop()
            self.post_stats(collector.get_result())

    def build_docker_container(self, image_name):
        c = self.console

        cwd = self.job.get('base_path', None)
        if cwd:
            cwd = os.path.join('/repo', cwd)
        else:
            cwd = "/repo"

        try:
            c.header("Build container", show=True)

            cmd = ['docker', 'build', '-t', image_name, '.', '-f', self.job['dockerfile']]

            if 'build_arguments' in self.job and self.job['build_arguments']:
                for name, value in self.job['build_arguments'].iteritems():
                    cmd += ['--build-arg', '%s=%s' % (name, value)]

            c.execute(cmd, cwd=cwd, show=True)
        except:
            raise Failure("Failed to build the container")

    def run_container(self, c):
        for dep in self.deployments:
            try:
                if dep['type'] == 'aws-ecr':
                    login_env = {
                        'AWS_ACCESS_KEY_ID': dep['access_key'],
                        'AWS_SECRET_ACCESS_KEY': dep['secret_key'],
                        'AWS_DEFAULT_REGION': dep['region'],
                        'PATH': os.environ['PATH']
                    }

                    c.execute(['/usr/local/bin/ecr_login.sh'], show=True, env=login_env)
                elif dep['type'] == 'docker-registry' and 'username' in dep:
                    host = dep['host']
                    c.execute(['docker', 'login', '-u', dep['username'],
                               '-p', dep['password'], host], show=False)
            except Exception as e:
                raise Failure("Failed to login to registry: " + e.message)


        image_name = get_registry_name() + '/' \
                     + self.project['id'] + '/' \
                     + self.job['name'] \
                     + ':build_%s' % self.build['build_number']

        self.build_docker_container(image_name)
        self.run_docker_container(image_name)
        self.deploy_container(image_name)
        self.push_container(image_name)

        c.header("Finished succesfully", show=True)

    def parse_infrabox_json(self, path):
        with open(path, 'r') as f:
            data = None
            try:
                data = json.load(f)
                validate_json(data)
            except Exception as e:
                raise Failure(e.__str__())

            return data

    def check_file_exist(self, data, base_path="/repo"):
        jobs = data.get('jobs', [])
        for job in jobs:
            job_type = job['type']

            if job_type == "docker":
                dockerfile = job['docker_file']
                p = os.path.join(base_path, dockerfile)
                if not os.path.exists(p):
                    raise Failure("%s does not exist" % p)

            if job_type == "docker-compose":
                composefile = job['docker_compose_file']
                p = os.path.join(base_path, composefile)
                if not os.path.exists(p):
                    raise Failure("%s does not exist" % p)

                # validate it
                try:
                    create_from(p)
                except Exception as e:
                    raise Failure("%s: %s" % (p, e.message))

            if job_type == "workflow":
                workflowfile = job['infrabox_file']
                p = os.path.join(base_path, workflowfile)
                if not os.path.exists(p):
                    raise Failure("%s does not exist" % p)

    def rewrite_depends_on(self, data):
        for job in data['jobs']:
            for i in range(0, len(job.get('depends_on', []))):
                d = job['depends_on'][i]

                if not isinstance(d, dict):
                    job['depends_on'][i] = {"job": d, "on": ["finished"]}
                    continue

                on = d['on']
                for n in range(0, len(on)):
                    if on[n] == "*":
                        d['on'] = ["finished", "error", "failure", "skipped"]
                        break

    def get_job_list(self, data, c, repo, parent_name="",
                     base_path=None,
                     repo_path='/repo', infrabox_paths=None):
        #pylint: disable=too-many-locals

        if not infrabox_paths:
            infrabox_paths = {}

        self.rewrite_depends_on(data)

        jobs = []
        for job in data['jobs']:
            job['id'] = str(uuid.uuid4())
            job['avg_duration'] = 0
            job['repo'] = repo
            job['base_path'] = base_path

            if parent_name != '':
                job['name'] = parent_name + "/" + job['name']

                deps = job.get('depends_on', [])
                for x in xrange(0, len(deps)):
                    deps[x]['job'] = parent_name + "/" + deps[x]['job']

            job_name = job['name']
            if job['type'] != "workflow" and job['type'] != "git":
                jobs.append(job)
                continue

            if job['type'] == "git":
                c.header("Clone repo %s" % job['clone_url'], show=True)
                new_repo_path = os.path.join('/tmp', job_name)
                c.execute(['rm', '-rf', new_repo_path])

                try:
                    c.execute(('git', 'clone', job['clone_url'],
                               new_repo_path), show=True)

                    c.execute(('git', 'checkout', '-qf', job['commit']), show=True, cwd=new_repo_path)
                except Exception as e:
                    raise Failure(e.__str__())

                c.header("Parsing infrabox.json", show=True)
                p = os.path.join(new_repo_path, 'infrabox.json')

                if p in infrabox_paths:
                    raise Failure("Recursive include detected")

                infrabox_paths[p] = True
                c.collect("file: %s" % p)
                yml = self.parse_infrabox_json(p)

                git_repo = {
                    "clone_url": job['clone_url'],
                    "commit": job['commit']
                }

                self.check_file_exist(yml, new_repo_path)
                sub = self.get_job_list(yml, c, git_repo, parent_name=job_name,
                                        repo_path=new_repo_path,
                                        infrabox_paths=infrabox_paths)

                del infrabox_paths[p]
            else:
                c.header("Parsing infrabox.json", show=True)
                p = os.path.join(repo_path, base_path or "", job['infrabox_file'])
                c.collect("file: %s\n" % p)
                bp = os.path.join(base_path or "", os.path.dirname(job['infrabox_file']))
                c.collect("basepath: %s\n" % bp)

                if p in infrabox_paths:
                    raise Failure("Recursive include detected")

                infrabox_paths[p] = True

                yml = self.parse_infrabox_json(p)
                self.check_file_exist(yml, base_path=os.path.dirname(p))

                sub = self.get_job_list(yml, c, repo,
                                        parent_name=job_name,
                                        base_path=bp,
                                        repo_path=repo_path)

                del infrabox_paths[p]

            # every sub job which does not have a parent
            # should be a child of the current job
            job_with_children = {}
            for s in sub:
                deps = s.get('depends_on', [])
                if len(deps) == 0:
                    s['depends_on'] = job.get('depends_on', [])

                for d in deps:
                    job_with_children[d['job']] = True

                # overwrite env vars if set
                if 'environment' in job:
                    for n, v in job['environment'].iteritems():
                        if 'environment' not in s:
                            s['environment'] = {}

                        s['environment'][n] = v

            jobs += sub

            # add a wait job to all sub jobs
            # which don't have a child, so we have
            # one 'final' job
            final_job = {
                "type": "wait",
                "name": job_name,
                "depends_on": [],
                "id": str(uuid.uuid4())
            }

            for s in sub:
                sub_name = s['name']
                if sub_name not in job_with_children:
                    final_job['depends_on'].append({"job": sub_name, "on": ["finished"]})

            jobs.append(final_job)

        return jobs

def main():
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DOCKER_REGISTRY_ADMIN_USERNAME')
    get_env('INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD')
    get_env('INFRABOX_DOCKER_REGISTRY_URL')
    get_env('INFRABOX_DASHBOARD_URL')
    get_env('INFRABOX_GENERAL_NO_CHECK_CERTIFICATES')
    get_env('INFRABOX_LOCAL_CACHE_ENABLED')
    get_env('INFRABOX_JOB_MAX_OUTPUT_SIZE')
    get_env('INFRABOX_JOB_API_URL')

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--type', choices=['create', 'run'], help="job type")

    args = parser.parse_args()
    console = ApiConsole()

    try:
        j = RunJob(console, args.type)
        j.main()
        j.console.flush()
        j.update_status('finished')
    except Failure as e:
        j.console.collect('## Failure', show=True)
        j.console.collect(e.message, show=True)
        j.console.flush()
        j.update_status('failure')
    except Exception as e:
        print_stackdriver()
        j.console.collect('## An error occured', show=True)
        j.console.collect(str(e), show=True)
        j.console.flush()
        j.update_status('error')

if __name__ == "__main__":
    try:
        main()
    except:
        print_stackdriver()
