#!/usr/bin/python
# pylint: disable=dangerous-default-value

import os
import shutil
import traceback
import json
import subprocess
import logging
import uuid
import argparse
import requests
import yaml

from pyinfrabox.infrabox import validate_json
from pyinfrabox.docker_compose import create_from

from infrabox_job.stats import StatsCollector
from infrabox_job.process import ApiConsole, Failure
from infrabox_job.job import Job

def makedirs(path):
    os.makedirs(path)
    os.chmod(path, 0o777)

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
        # the run_job.py container.
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
                }
            }

            if self.project['type'] == 'github':
                o['commit'] = {}
                o['commit']["branch"] = self.commit['branch']
                o['commit']["id"] = self.commit['id']
                o['build']["url"] = os.environ['INFRABOX_DASHBOARD_URL'] + '/dashboard/project/' + self.project['id'] + '/commit/' + self.commit['id']

            if self.project['type'] == 'upload':
                o['build']["url"] = os.environ['INFRABOX_DASHBOARD_URL'] + '/dashboard/project/' + self.project['id'] + '/build/' + str(self.build['build_number'])

            json.dump(o, out)


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

        if self.job['repo'] or self.project['type'] == 'github':
            if self.job['repo']:
                clone_url = self.job['repo']['clone_url']
                private = False
            else:
                clone_url = self.repository['clone_url']
                private = self.repository['private']

                if private:
                    clone_url = clone_url.replace('github.com',
                                                  '%s@github.com' % self.repository['github_api_token'])

            c.execute(['rm', '-rf', 'repo'], show=True)

            cmd = ['git', 'clone', '--depth=10']
            if self.commit['branch']:
                cmd += ['--single-branch', '-b', self.commit['branch']]

            c.header("Clone repository", show=True)
            cmd += [clone_url, '/repo']

            c.collect(' '.join(cmd), show=True)
            c.execute(cmd, show=True)

            if 'repo' in self.job and self.job['repo'] and 'ref' in self.job['repo'] and self.job['repo']['ref']:
                cmd = ['git', 'fetch', '--depth=10', clone_url, self.job['repo']['ref']]
                c.collect(' '.join(cmd), show=True)
                c.execute(cmd, show=True, cwd="/repo")

            c.header("Checkout commit", show=True)
            c.execute(['git', 'checkout', '-qf', '-b', 'job', self.commit['id']],
                      cwd="/repo", show=True)

            c.header("Init submodules", show=True)
            c.execute(['git', 'submodule', 'init'], cwd="/repo", show=True)
            c.execute(['git', 'submodule', 'update'], cwd="/repo", show=True)
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

        if 'generator' in data:
            c.header("Running generator", show=True)
            self.job['dockerfile'] = data['generator']['docker_file']
            c.collect("Using docker file: %s \n" % self.job['dockerfile'], show=True)

            job_name = self.job['name']
            self.job['name'] = "generator"
            self.run_container(c)
            self.job['name'] = job_name

            infrabox_json_path = os.path.join(self.infrabox_output_dir, "infrabox.json")
            if not os.path.exists(infrabox_json_path):
                raise Failure("Generator job did not create /infrabox/output/infrabox.json")

            shutil.copyfile(infrabox_json_path, "/repo/infrabox.json")

            data = self.parse_infrabox_json('/repo/infrabox.json')
            self.check_file_exist(data)

        c.header("Creating jobs", show=True)
        jobs = self.get_job_list(data, c, self.job['repo'], infrabox_paths={"/repo/infrabox.json": True})
        self.check_quota(jobs)
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

    def main_run_job(self):
        c = self.console
        self.create_jobs_json()

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
                c.collect("input found: %s\n" % dep['name'])
                c.execute(['ls', '-alh', storage_input_file_tar], show=True)
                infrabox_input_dir = os.path.join(self.infrabox_inputs_dir, dep['name'].split('/')[-1])
                os.makedirs(infrabox_input_dir)
                self.uncompress(storage_input_file_tar, infrabox_input_dir, c)
                os.remove(storage_input_file_tar)
            else:
                c.collect("no input found\n")

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

        if self.job['type'] == 'run_project_container':
            self.run_container(c)
        elif self.job['type'] == 'run_docker_compose':
            self.run_docker_compose(c)
        else:
            raise Exception('Unknown job type')

        # Upload test results
        c.header("Uploading test results", show=True)
        if os.path.exists(self.infrabox_testresult_dir):
            files = self.get_files_in_dir(self.infrabox_testresult_dir, ".json")

            for f in files:
                tr_path = os.path.join(self.infrabox_testresult_dir, f)
                c.collect("%s\n" % tr_path, show=True)
                r = requests.post("http://localhost:5000/testresult",
                                  files={"data": open(tr_path)}, timeout=10)
                c.collect("%s\n" % r.text, show=True)

        # Upload markdown files
        c.header("Uploading markdown files", show=False)
        if os.path.exists(self.infrabox_markdown_dir):
            files = self.get_files_in_dir(self.infrabox_markdown_dir, ".md")

            for f in files:
                file_name = os.path.basename(f)
                r = requests.post("http://localhost:5000/markdown",
                                  files={file_name: open(os.path.join(self.infrabox_markdown_dir, f))}, timeout=10)
                c.collect("%s\n" % r.text, show=False)

        # Upload markup files
        c.header("Uploading markup files", show=True)
        if os.path.exists(self.infrabox_markup_dir):
            files = self.get_files_in_dir(self.infrabox_markup_dir, ".json")

            for f in files:
                file_name = os.path.basename(f)
                f = open(os.path.join(self.infrabox_markup_dir, f))
                r = requests.post("http://localhost:5000/markup",
                                  files={file_name: f}, timeout=10)
                c.collect(f.read(), show=True)
                c.collect("%s\n" % r.text, show=True)

        # Upload badge files
        c.header("Uploading badge files", show=True)
        if os.path.exists(self.infrabox_badge_dir):
            files = self.get_files_in_dir(self.infrabox_badge_dir, ".json")

            for f in files:
                file_name = os.path.basename(f)
                r = requests.post("http://localhost:5000/badge",
                                  files={file_name: open(os.path.join(self.infrabox_badge_dir, f))}, timeout=10)
                c.collect("%s\n" % r.text, show=True)

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

        try:
            self.environment['PATH'] = os.environ['PATH']
            c.execute(['docker-compose', '-f', compose_file_new, 'build'],
                      show=True, env=self.environment)
            c.header("Run docker-compose", show=True)

            cwd = self.job.get('base_path', None)
            if cwd:
                cwd = os.path.join('/repo', cwd)

            collector = StatsCollector()

            c.execute(['docker-compose', '-f', compose_file_new, 'up',
                       '--abort-on-container-exit'], env=self.environment, show=True, cwd=cwd)
            c.execute(['docker-compose', '-f', compose_file_new, 'ps'], env=self.environment, cwd=cwd)
            c.execute(['get_compose_exit_code.sh', compose_file_new], env=self.environment, cwd=cwd)

            collector.stop()
            self.post_stats(collector.get_result())
        except:
            raise Failure("Failed to build and run container")

        return True

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
                else:
                    raise Exception("Not implemented")
            except Exception as e:
                raise Failure("Failed to login to registry: " + e.message)


        image_name = os.environ['INFRABOX_DOCKER_REGISTRY_URL'] + '/' + self.project['id'] + '/' + self.job['name'] + ':build_%s' % self.build['build_number']

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

        collector = StatsCollector()

        try:
            if not self.job['build_only']:
                c.header("Run container", show=True)
                container_name = self.job['id']
                cmd = ['docker', 'run', '--name', container_name, '-v', self.data_dir + ':/infrabox']

                # Add local cache
                if os.environ['INFRABOX_LOCAL_CACHE_ENABLED'] == 'true':
                    cmd += ['-v', "/local-cache:/infrabox/local-cache"]

                # add env vars
                for name, value in self.environment.iteritems():
                    cmd += ['-e', '%s=%s' % (name, value)]

                cmd += [image_name]
                c.execute(cmd, show=True)

                if self.job['commit_after_run']:
                    c.execute(("docker", "commit", container_name, image_name))
        except:
            raise Failure("Container run exited with error")
        finally:
            collector.stop()
            self.post_stats(collector.get_result())

        # Scan container
        if self.job['scan_container'] and os.environ['INFRABOX_CLAIR_ENABLED'] == "true":
            c.header("Scanning container for vulnerabilities", show=True)
            c.execute(['python', '/usr/local/bin/analyze.py',
                       '--image', image_name,
                       '--output', os.path.join(self.infrabox_markup_dir, "Container Scan.json")],
                      show=True)

        # Deploying
        c.header("Deploying", show=True)
        if not self.deployments:
            c.collect("No deployments configured\n", show=True)

        for dep in self.deployments:
            dep_image_name = dep['host'] + '/' + dep['repository'] + ':build_%s' % self.build['build_number']
            c.execute(['docker', 'tag', image_name, dep_image_name], show=True)
            c.execute(['docker', 'push', dep_image_name], show=True)

        # Pushing
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
                           os.environ['INFRABOX_DOCKER_REGISTRY_URL']], show=False)

                c.execute(['docker', 'push', image_name], show=True)
        except Exception as e:
            raise Failure(e.__str__())

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
        if 'generator' in data:
            p = os.path.join(base_path, data['generator']['docker_file'])
            if not os.path.exists(p):
                raise Failure("%s does not exist" % p)



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

    def get_job_list(self, data, c, repo, parent_name="",
                     base_path=None,
                     repo_path='/repo', infrabox_paths={}):

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
                    deps[x] = parent_name + "/" + deps[x]

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
                    job_with_children[d] = True

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
                    final_job['depends_on'].append(sub_name)

            jobs.append(final_job)

        return jobs

    def check_quota(self, jobs):
        max_jobs_per_build = self.quota['max_jobs_per_build']
        if len(jobs) > max_jobs_per_build:
            raise Failure("Quota: max jobs per build is %s, but you requested %s" % (max_jobs_per_build, len(jobs)))

        for j in jobs:
            if j['type'] in ('wait', 'workflow', 'git'):
                continue

            l = j['resources']['limits']
            max_cpu = self.quota['max_cpu_per_job']
            if l['cpu'] > max_cpu:
                raise Failure("Quota: max cpu per job is %s, but you requested %s" % (max_cpu, l['cpu']))

            max_memory = self.quota['max_memory_per_job']
            if l['cpu'] > max_cpu:
                raise Failure("Quota: max memory per job is %s, but you requested %s" % (max_memory, l['memory']))

def print_stackdriver():
    if 'INFRABOX_GENERAL_LOG_STACKDRIVER' in os.environ and os.environ['INFRABOX_GENERAL_LOG_STACKDRIVER'] == 'true':
        print json.dumps({
            "serviceContext": {
                "service": os.environ.get('INFRABOX_SERVICE', 'unknown'),
                "version": os.environ.get('INFRABOX_VERSION', 'unknown')
            },
            "message": traceback.format_exc(),
            "severity": 'ERROR'
        })
    else:
        print traceback.format_exc()

def main():
    if 'INFRABOX_SERVICE' not in os.environ:
        raise Exception("INFRABOX_SERVICE not set")

    if 'INFRABOX_VERSION' not in os.environ:
        raise Exception("INFRABOX_VERSION not set")

    if 'INFRABOX_DOCKER_REGISTRY_ADMIN_USERNAME' not in os.environ:
        raise Exception('INFRABOX_DOCKER_REGISTRY_ADMIN_USERNAME not set')

    if 'INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD' not in os.environ:
        raise Exception('INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD not set')

    if 'INFRABOX_DOCKER_REGISTRY_URL' not in os.environ:
        raise Exception('INFRABOX_DOCKER_REGISTRY_URL not set')

    if 'INFRABOX_DASHBOARD_URL' not in os.environ:
        raise Exception('INFRABOX_DASHBOARD_URL not set')

    if 'INFRABOX_GENERAL_NO_CHECK_CERTIFICATES' not in os.environ:
        raise Exception('INFRABOX_GENERAL_NO_CHECK_CERTIFICATES not set')

    if 'INFRABOX_LOCAL_CACHE_ENABLED' not in os.environ:
        raise Exception('INFRABOX_LOCAL_CACHE_ENABLED not set')

    if 'INFRABOX_JOB_MAX_OUTPUT_SIZE' not in os.environ:
        raise Exception('INFRABOX_JOB_MAX_OUTPUT_SIZE not set')

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--type', choices=['create', 'run'], help="job type")

    args = parser.parse_args()
    console = ApiConsole()

    if os.environ['INFRABOX_GENERAL_NO_CHECK_CERTIFICATES'] == 'true':
        console.execute(('git', 'config', '--global', 'http.sslVerify', 'false'), show=False)

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
        j.console.flush()
        j.update_status('error')

if __name__ == "__main__":
    try:
        main()
    except:
        print_stackdriver()
