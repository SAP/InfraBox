#!/usr/bin/python
#pylint: disable=too-many-lines,attribute-defined-outside-init,too-many-public-methods,too-many-locals
import os
import sys
import shutil
import time
import json
import subprocess
import uuid
import base64
import traceback
import requests

from pyinfrabox.infrabox import validate_json
from pyinfrabox.docker_compose import create_from

from infrabox_job.stats import StatsCollector
from infrabox_job.process import ApiConsole, Failure
from infrabox_job.job import Job

from pyinfraboxutils.testresult import Parser as TestresultParser
from pyinfraboxutils.coverage import Parser as CoverageParser
from pyinfraboxutils import get_env, print_stackdriver
from pyinfraboxutils import get_logger
logger = get_logger('scheduler')

def makedirs(path):
    os.makedirs(path)
    os.chmod(path, 0o777)

def get_registry_name():
    n = os.environ['INFRABOX_ROOT_URL'].replace('https://', '')
    n = n.replace('http://', '')
    return n

class RunJob(Job):
    def __init__(self, console):
        Job.__init__(self)
        self.console = console
        self.storage_dir = '/tmp/storage'

        if os.path.exists(self.storage_dir):
            shutil.rmtree(self.storage_dir)

        os.makedirs(self.storage_dir)

        self.mount_repo_dir = os.environ.get('INFRABOX_JOB_REPO_MOUNT_PATH', '/repo')
        self.mount_data_dir = self.mount_repo_dir + '/.infrabox'

    def create_infrabox_directories(self):
        if os.path.exists(self.mount_data_dir):
            shutil.rmtree(self.mount_data_dir, ignore_errors=True)

        #
        # /tmp/infrabox is mounted to the same path on the host
        # So we can use it to transfer data between the job and
        # the job.py container.
        #

        # <data_dir>/cache is mounted in the job to /infrabox/cache
        self.infrabox_cache_dir = os.path.join(self.mount_data_dir, 'cache')
        makedirs(self.infrabox_cache_dir)

        # <data_dir>/inputs is mounted in the job to /infrabox/inputs
        self.infrabox_inputs_dir = os.path.join(self.mount_data_dir, 'inputs')
        makedirs(self.infrabox_inputs_dir)

        # <data_dir>/output is mounted in the job to /infrabox/output
        self.infrabox_output_dir = os.path.join(self.mount_data_dir, 'output')
        makedirs(self.infrabox_output_dir)

        # <data_dir>/upload is mounted in the job to /infrabox/upload
        self.infrabox_upload_dir = os.path.join(self.mount_data_dir, 'upload')
        makedirs(self.infrabox_upload_dir)

        # <data_dir>/upload/testresult is mounted in the job to /infrabox/upload/testresult
        self.infrabox_testresult_dir = os.path.join(self.infrabox_upload_dir, 'testresult')
        makedirs(self.infrabox_testresult_dir)

        # <data_dir>/upload/coverage is mounted in the job to /infrabox/upload/coverage
        self.infrabox_coverage_dir = os.path.join(self.infrabox_upload_dir, 'coverage')
        makedirs(self.infrabox_coverage_dir)

        # <data_dir>/upload/markdown is mounted in the job to /infrabox/upload/markdown
        self.infrabox_markdown_dir = os.path.join(self.infrabox_upload_dir, 'markdown')
        makedirs(self.infrabox_markdown_dir)

        # <data_dir>/upload/markup is mounted in the job to /infrabox/upload/markup
        self.infrabox_markup_dir = os.path.join(self.infrabox_upload_dir, 'markup')
        makedirs(self.infrabox_markup_dir)

        # <data_dir>/upload/badge is mounted in the job to /infrabox/upload/badge
        self.infrabox_badge_dir = os.path.join(self.infrabox_upload_dir, 'badge')
        makedirs(self.infrabox_badge_dir)

        # <data_dir>/upload/archive is mounted in the job to /infrabox/upload/archive
        self.infrabox_archive_dir = os.path.join(self.infrabox_upload_dir, 'archive')
        makedirs(self.infrabox_archive_dir)

    def create_jobs_json(self):
        # create job.json
        infrabox_job_json = os.path.join(self.mount_data_dir, 'job.json')
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
                    "url": os.environ['INFRABOX_ROOT_URL'] \
                           + '/dashboard/#/project/' + self.project['name'] \
                           + '/build/' + str(self.build['build_number']) \
                           + '/' + str(self.build['restart_counter'])
                }
            }

            if self.project['type'] == 'github':
                o['commit'] = {}
                o['commit']["branch"] = self.commit['branch']
                o['commit']["id"] = self.commit['id']

            json.dump(o, out)

    def flush(self):
        self.console.flush()

    def compress(self, source, output):
        subprocess.check_call("tar cf - --directory %s . | pigz -n > %s" % (source, output), shell=True)

    def uncompress(self, source, output, c):
        cmd = "pigz -dc %s | tar x -C %s" % (source, output)
        c.collect(cmd, show=True)
        subprocess.check_call(cmd, shell=True)

    def get_files_in_dir(self, d, ending=None):
        result = []
        for root, _, files in os.walk(d):
            for f in files:
                if ending:
                    if not f.endswith(ending):
                        continue

                result.append(os.path.join(root, f))

        return result

    def clone_repo(self, commit, clone_url, branch, ref, clone_all, sub_path=None, submodules=True):
        c = self.console
        mount_repo_dir = self.mount_repo_dir

        if sub_path:
            mount_repo_dir = os.path.join(mount_repo_dir, sub_path)

        if os.environ['INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES'] == 'true':
            c.execute(('git', 'config', '--global', 'http.sslVerify', 'false'), show=True)

        cmd = ['git', 'clone']

        if not clone_all:
            cmd += ['--depth=10']

            if branch:
                cmd += ['--single-branch', '-b', branch]

        cmd += [clone_url, mount_repo_dir]

        exc = None
        for _ in range(0, 3):
            exc = None
            try:
                c.execute(cmd, show=True)
                break
            except Exception as e:
                exc = e
                time.sleep(5)

        if exc:
            raise exc

        if ref:
            cmd = ['git', 'fetch', '--depth=10', clone_url, ref]
            c.execute(cmd, cwd=mount_repo_dir, show=True)

        c.execute(['git', 'config', 'remote.origin.url', clone_url], cwd=mount_repo_dir, show=True)
        c.execute(['git', 'config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*'],
                  cwd=mount_repo_dir, show=True)

        if not clone_all:
            c.execute(['git', 'fetch', 'origin', commit], cwd=mount_repo_dir, show=True)

        cmd = ['git', 'checkout', '-qf', commit]

        c.execute(cmd, cwd=mount_repo_dir, show=True)

        if submodules:
            c.execute(['git', 'submodule', 'init'], cwd=mount_repo_dir, show=True)
            c.execute(['git', 'submodule', 'update'], cwd=mount_repo_dir, show=True)


    def get_source(self):
        c = self.console

        if self.job['repo']:
            repo = self.job['repo']
            clone_url = repo['clone_url']
            branch = repo.get('branch', None)
            private = repo.get('github_private_repo', False)
            clone_all = repo.get('clone_all', False)
            ref = repo.get('ref', None)

            definition = self.job['definition']

            if not definition:
                definition = {}

            def_repo = definition.get('repository', {})
            repo_clone = def_repo.get('clone', True)
            repo_submodules = def_repo.get('submodules', True)

            commit = repo['commit']

            if self.job['type'] == 'create_job_matrix':
                repo_submodules = False

            if not repo_clone:
                return

            if private:
                clone_url = clone_url.replace('github.com',
                                              '%s@github.com' % self.repository['github_api_token'])

            self.clone_repo(commit, clone_url, branch, ref, clone_all, submodules=repo_submodules)
        elif self.project['type'] == 'upload':
            c.collect("Downloading Source")
            storage_source_zip = os.path.join(self.storage_dir, 'source.zip')
            self.get_file_from_api_server('/source', storage_source_zip)

            if not os.path.exists(self.mount_repo_dir):
                os.makedirs(self.mount_repo_dir)
            else:
                c.collect('Source already exists, deleting it')
                c.execute(['rm', '-rf', self.mount_repo_dir + '/*'])

            c.execute(['unzip', storage_source_zip, '-d', self.mount_repo_dir])
        elif self.project['type'] == 'test':
            pass
        else:
            raise Exception('Unknown project type')

        c.execute(['chmod', '-R', 'a+rwX', self.mount_repo_dir])

    def main_create_jobs(self):
        c = self.console

        ib_json = os.path.join(self.mount_repo_dir, 'infrabox.json')
        if not os.path.isfile(ib_json):
            raise Failure("infrabox.json not found")

        c.header("Parsing infrabox.json", show=True)
        data = self.parse_infrabox_json(ib_json)
        self.check_file_exist(data, self.mount_repo_dir)

        c.header("Creating jobs", show=True)
        jobs = self.get_job_list(data, c, self.job['repo'], infrabox_paths={ib_json: True})

        if jobs:
            self.create_jobs(jobs)
            c.collect("Done creating jobs\n")
        else:
            c.collect("No jobs\n")

    def check_container_crashed(self):
        # if the started file exists already this
        # means the container crashed and restarted.
        # then we just mark it as failed.
        p = os.path.join(self.mount_data_dir, "started")

        if os.path.exists(p):
            raise Failure("Container crashed")
        else:
            with open(p, 'w+') as f:
                f.write("started")

    def main(self):
        self.load_data()

        # Show environment
        self.console.collect("Environment:\n", show=True)
        for name, value in self.env_vars.iteritems():
            self.console.collect("%s=%s\n" % (name, value), show=True)

        self.console.collect("\n", show=True)

        # Show secrets
        if self.secrets:
            self.console.collect("Secrets:\n", show=True)
            for name, _ in self.secrets.iteritems():
                self.console.collect("%s=*****\n" % name, show=True)
            self.console.collect("\n", show=True)

        # Show Registries
        if self.registries:
            self.console.collect("Registries:\n", show=True)
            for r in self.registries:
                self.console.collect("%s\n" % r['host'], show=True)
            self.console.collect("\n", show=True)

        # Show Deployments
        if self.deployments:
            self.console.collect("Deployments:\n", show=True)
            for d in self.deployments:
                self.console.collect("%s\n" % d['host'], show=True)
            self.console.collect("\n", show=True)

        self.get_source()
        self.create_infrabox_directories()

        if self.job['type'] == 'create_job_matrix':
            self.main_create_jobs()
        else:
            self.main_run_job()

    def convert_coverage_result(self, f):
        parser = CoverageParser(f)
        r = parser.parse(self.infrabox_badge_dir)
        return r

    def upload_archive(self):
        c = self.console

        if os.path.exists(self.infrabox_archive_dir):
            files = self.get_files_in_dir(self.infrabox_archive_dir)

            if files:
                c.collect("Uploading /infrabox/upload/archive", show=True)

                for f in files:
                    c.collect("%s\n" % f, show=True)
                    self.post_file_to_api_server("/archive", f, filename=f.replace(self.infrabox_upload_dir, ''))

        if os.path.exists(self.infrabox_testresult_dir):
            files = self.get_files_in_dir(self.infrabox_testresult_dir)

            if files:

                for f in files:
                    c.collect("%s\n" % f, show=True)


    def upload_coverage_results(self):
        c = self.console
        if not os.path.exists(self.infrabox_coverage_dir):
            return

        files = self.get_files_in_dir(self.infrabox_coverage_dir, ending=".xml")
        for f in files:
            c.collect("%s\n" % f, show=True)
            converted_result = self.convert_coverage_result(f)
            file_name = os.path.basename(f)

            mu_path = os.path.join(self.infrabox_markup_dir, file_name + '.json')

            with open(mu_path, 'w') as out:
                json.dump(converted_result, out)

    def convert_test_result(self, f):
        parser = TestresultParser(f)
        r = parser.parse(self.infrabox_badge_dir)

        out = f + '.json'
        with open(out, 'w') as testresult:
            json.dump(r, testresult)

        return out

    def upload_test_results(self):
        c = self.console
        if not os.path.exists(self.infrabox_testresult_dir):
            return

        c.collect("Uploading /infrabox/upload/testresult", show=True)
        files = self.get_files_in_dir(self.infrabox_testresult_dir, ending=".xml")
        for f in files:
            c.collect("%s\n" % f, show=True)
            self.post_file_to_api_server("/archive", f, filename=f.replace(self.infrabox_upload_dir, ''))

            try:
                converted_result = self.convert_test_result(f)
                self.post_file_to_api_server("/testresult", converted_result, filename='data')
            except Exception as e:
                self.console.collect("Failed to parse test result: %s \n" % e, show=True)


    def upload_markdown_files(self):
        c = self.console
        if not os.path.exists(self.infrabox_markdown_dir):
            return

        files = self.get_files_in_dir(self.infrabox_markdown_dir, ending=".md")
        for f in files:
            c.collect("%s\n" % f, show=True)

            file_name = os.path.basename(f)
            self.post_file_to_api_server("/markdown", f, filename=file_name)

    def upload_markup_files(self):
        c = self.console
        if not os.path.exists(self.infrabox_markup_dir):
            return

        files = self.get_files_in_dir(self.infrabox_markup_dir, ending=".json")
        for f in files:
            c.collect("%s\n" % f, show=True)

            file_name = os.path.basename(f)
            self.post_file_to_api_server("/markup", f, filename=file_name)

    def upload_badge_files(self):
        c = self.console
        if not os.path.exists(self.infrabox_badge_dir):
            return

        files = self.get_files_in_dir(self.infrabox_badge_dir, ending=".json")

        for f in files:
            c.collect("%s\n" % f, show=True)

            file_name = os.path.basename(f)
            self.post_file_to_api_server("/badge", f, filename=file_name)

    def create_dynamic_jobs(self):
        c = self.console
        infrabox_json_path = os.path.join(self.infrabox_output_dir, 'infrabox.json')
        infrabox_context = os.path.dirname(infrabox_json_path)

        if os.path.exists(infrabox_json_path):
            c.header("Creating jobs", show=True)
            data = self.parse_infrabox_json(infrabox_json_path)
            self.check_file_exist(data, infrabox_context)
            jobs = self.get_job_list(data, c, self.job['repo'],
                                     infrabox_paths={infrabox_json_path: True},
                                     infrabox_context=infrabox_context)
            c.collect(json.dumps(jobs, indent=4), show=True)

            if jobs:
                self.create_jobs(jobs)
                c.collect("Done creating jobs\n")
            else:
                c.collect("No jobs\n")

    def _get_size(self, start_path):
        total_size = 0
        for dirpath, _, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    def main_run_job(self):
        c = self.console
        self.create_jobs_json()

        # base dir for inputs
        storage_inputs_dir = os.path.join(self.storage_dir, 'inputs')

        # Sync deps
        c.collect("Syncing inputs:", show=True)
        for dep in self.parents:
            storage_input_file_dir = os.path.join(storage_inputs_dir, dep['id'])
            os.makedirs(storage_input_file_dir)

            storage_input_file_tar = os.path.join(storage_input_file_dir, 'output.tar.gz')
            self.get_file_from_api_server('/output/%s' % dep['id'], storage_input_file_tar)

            if os.path.isfile(storage_input_file_tar):
                c.collect("output found for %s\n" % dep['name'], show=True)
                infrabox_input_dir = os.path.join(self.infrabox_inputs_dir, dep['name'].split('/')[-1])
                os.makedirs(infrabox_input_dir)
                self.uncompress(storage_input_file_tar, infrabox_input_dir, c)
                c.execute(['ls', '-alh', infrabox_input_dir], show=True)
                os.remove(storage_input_file_tar)
            else:
                c.collect("no output found for %s\n" % dep['name'], show=True)
        c.collect("\n", show=True)

        # <storage_dir>/cache is synced with the corresponding
        # Storage path which stores the compressed cache
        storage_cache_dir = os.path.join(self.storage_dir, 'cache')
        os.makedirs(storage_cache_dir)

        storage_cache_tar = os.path.join(storage_cache_dir, 'cache.tar.gz')

        c.collect("Syncing cache:", show=True)
        if not self.job['definition'].get('cache', {}).get('data', True):
            c.collect("Not downloading cache, because cache.data has been set to false", show=True)
        else:
            self.get_file_from_api_server("/cache", storage_cache_tar)

            if os.path.isfile(storage_cache_tar):
                c.collect("Unpacking cache", show=True)
                try:
                    c.execute(['time', 'tar', '-zxf', storage_cache_tar, '-C', self.infrabox_cache_dir], show=True)
                except:
                    c.collect("Failed to unpack cache\n", show=True)
                os.remove(storage_cache_tar)
            else:
                c.collect("no cache found\n", show=True)
        c.collect("\n", show=True)

        try:
            if self.job['definition']['type'] == 'docker':
                self.run_job_docker(c)
            elif self.job['definition']['type'] == 'docker-image':
                self.run_job_docker_image(c)
            elif self.job['definition']['type'] == 'docker-compose':
                self.run_job_docker_compose(c)
            else:
                raise Exception('Unknown job type: %s' % self.job['type'])
        except:
            raise
        finally:
            self.upload_coverage_results()
            self.upload_test_results()
            self.upload_markdown_files()
            self.upload_markup_files()
            self.upload_badge_files()
            self.upload_archive()

        self.create_dynamic_jobs()

        # Compressing output
        c.collect("Uploading /infrabox/output", show=True)
        if os.path.isdir(self.infrabox_output_dir) and os.listdir(self.infrabox_output_dir):
            storage_output_dir = os.path.join(self.storage_dir, self.job['id'])
            os.makedirs(storage_output_dir)

            storage_output_tar = os.path.join(storage_output_dir, 'output.tar.gz')
            self.compress(self.infrabox_output_dir, storage_output_tar)
            file_size = os.stat(storage_output_tar).st_size

            max_output_size = os.environ['INFRABOX_JOB_MAX_OUTPUT_SIZE']
            c.collect("Output size: %s kb" % (file_size / 1024), show=True)
            if file_size > max_output_size:
                raise Failure("Output too large")

            self.post_file_to_api_server("/output", storage_output_tar)
        else:
            c.collect("Output is empty", show=True)

        c.collect("\n", show=True)

        # Compressing cache
        c.collect("Uploading /infrabox/cache", show=True)
        if not self.job['definition'].get('cache', {}).get('data', True):
            c.collect("Not updating cache, because cache.data has been set to false", show=True)
        else:
            if os.path.isdir(self.infrabox_cache_dir) and os.listdir(self.infrabox_cache_dir):
                self.compress(self.infrabox_cache_dir, storage_cache_tar)

                file_size = os.stat(storage_cache_tar).st_size

                max_output_size = os.environ['INFRABOX_JOB_MAX_OUTPUT_SIZE']
                c.collect("Output size: %s kb" % (file_size / 1024), show=True)
                if file_size > max_output_size:
                    raise Failure("Output too large")

                self.post_file_to_api_server('/cache', storage_cache_tar)
            else:
                c.collect("Cache is empty", show=True)
        c.collect("\n", show=True)

        shutil.rmtree(self.mount_data_dir, True)
        shutil.rmtree(self.infrabox_cache_dir, True)

    def run_job_docker_compose(self, c):
        c.header("Build containers", show=True)
        f = self.job['dockerfile']

        compose_file = os.path.normpath(os.path.join(self.job['definition']['infrabox_context'], f))
        compose_file_new = compose_file + ".infrabox.json"

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

            service_coverage_dir = os.path.join(self.infrabox_coverage_dir, service)
            makedirs(service_coverage_dir)

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
                "%s:/infrabox/upload/coverage" % service_coverage_dir,
            ]

            for v in compose_file_content['services'][service].get('volumes', []):
                v = v.replace('/infrabox/context', self.mount_repo_dir)
                service_volumes.append(v)

            # Mount /infrabox/context to the build context of the service if build.context
            # is set in the compose file for the service
            service_build = compose_file_content['services'][service].get('build', None)
            if service_build:
                service_build_context = service_build.get('context', None)
                if service_build_context:
                    build_context = os.path.join(os.path.dirname(compose_file), service_build_context)
                    service_volumes += ['%s:/infrabox/context' % build_context]

            if os.environ['INFRABOX_LOCAL_CACHE_ENABLED'] == 'true':
                service_volumes.append("/local-cache:/infrabox/local-cache")

            compose_file_content['services'][service]['volumes'] = service_volumes

            image_name = get_registry_name() + '/' \
                         + self.project['id'] + '/' \
                         + self.job['name'] + '/' \
                         + service

            image_name_latest = image_name + ':latest'
            build = compose_file_content['services'][service].get('build', None)

            if build:
                compose_file_content['services'][service]['image'] = image_name_latest
                compose_file_content['services'][service]['build']['cache_from'] = [image_name_latest]
                self.get_cached_image(image_name_latest)

        with open(compose_file_new, "w+") as out:
            json.dump(compose_file_content, out)

        collector = StatsCollector()

        try:
            try:
                c.execute(['docker-compose', '-f', compose_file_new, 'rm'],
                          env=self.environment)
            except Exception as e:
                logger.exception(e)


            self.environment['PATH'] = os.environ['PATH']
            c.execute(['docker-compose', '-f', compose_file_new, 'build'],
                      show=True, env=self.environment)
            c.header("Run docker-compose", show=True)


            cwd = self._get_build_context_current_job()

            c.execute(['docker-compose', '-f', compose_file_new, 'up',
                       '--abort-on-container-exit'], env=self.environment, show=True, cwd=cwd)
            c.execute(['docker-compose', '-f', compose_file_new, 'ps'], env=self.environment, cwd=cwd)
            c.execute(['get_compose_exit_code.sh', compose_file_new], env=self.environment, cwd=cwd)
        except:
            raise Failure("Failed to build and run container")
        finally:
            c.header("Finalize", show=True)

            try:
                collector.stop()
                self.post_stats(collector.get_result())
                c.execute(['docker-compose', '-f', compose_file_new, 'rm'],
                          env=self.environment)
            except Exception as e:
                logger.exception(e)

        for service in compose_file_content['services']:
            image_name = get_registry_name() + '/' \
                         + self.project['id'] + '/' \
                         + self.job['name'] + '/' \
                         + service

            image_name_latest = image_name + ':latest'

            build = compose_file_content['services'][service].get('build', None)
            if build:
                compose_file_content['services'][service]['image'] = service

            self.cache_docker_image(image_name_latest, image_name_latest)

        return True

    def _get_build_context_current_job(self):
        job_build_context = self.job['definition'].get('build_context', None)
        job_infrabox_context = self.job['definition']['infrabox_context']
        return self._get_build_context_impl(job_build_context, job_infrabox_context)

    def _get_build_context_impl(self, job_build_context, job_infrabox_context):
        # Default build context is the infrabox context
        build_context = job_infrabox_context

        if job_build_context:
            # job specified build context is alway relative to the infrabox context
            build_context = os.path.join(job_infrabox_context, job_build_context)

        build_context = os.path.join(self.mount_repo_dir, build_context)

        if not build_context.startswith(self.mount_repo_dir):
            raise Failure('Invalid build_context')

        return os.path.normpath(build_context)

    def deploy_container(self, image_name):
        c = self.console
        if not self.deployments:
            return

        c.header("Deploying", show=True)

        for dep in self.deployments:
            tag = dep.get('tag', 'build_%s' % self.build['build_number'])
            dep_image_name = dep['host'] + '/' + dep['repository'] + ":" + tag
            c.execute(['docker', 'tag', image_name, dep_image_name], show=True)

            self._login_registry(dep)
            c.execute(['docker', 'push', dep_image_name], show=True)
            self._logout_registry(dep)

    def login_docker_registry(self):
        c = self.console
        c.execute(['docker', 'login',
                   '-u', 'infrabox',
                   '-p', os.environ['INFRABOX_JOB_TOKEN'],
                   get_registry_name()], show=False)

    def logout_docker_registry(self):
        c = self.console
        c.execute(['docker', 'logout', get_registry_name()], show=False)

    def push_container(self, image_name):
        c = self.console

        cache_after_image = self.job['definition'].get('cache', {}).get('after_image', False)

        if not cache_after_image:
            return

        c.collect("Uploading after image to docker registry", show=True)

        try:
            if self.job['build_only']:
                c.collect("Not pushing container, because build_only is set.\n", show=True)
            else:
                self.login_docker_registry()
                c.execute(['docker', 'push', image_name], show=True)
                self.logout_docker_registry()
        except Exception as e:
            raise Failure(e.__str__())

    def run_docker_container(self, image_name):
        c = self.console
        collector = StatsCollector()

        container_name = self.job['id']
        cmd = ['docker', 'run', '--name', container_name]

        # Memory limit
        memory_limit = os.environ['INFRABOX_JOB_RESOURCES_LIMITS_MEMORY']
        cmd += ['-m', '%sm' % memory_limit]

        # repo mount
        cmd += ['-v', '%s:/infrabox' % self.mount_data_dir]

        # Mount context
        cmd += ['-v', '%s:/infrabox/context' % self._get_build_context_current_job()]

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
            cmd += ['-e', 'INFRABOX_RESOURCES_KUBERNETES_MASTER_URL=%s' %
                    os.environ['INFRABOX_RESOURCES_KUBERNETES_MASTER_URL']]

        # add services
        if os.path.exists('/var/run/infrabox.net/services'):
            cmd += ['-v', '/var/run/infrabox.net/services:/var/run/infrabox.net/services']

        cmd += ['--tmpfs', '/infrabox/tmpfs']

        # Add capabilities
        security_context = self.job['definition'].get('security_context', {})

        if security_context:
            capabilities = security_context.get('capabilities', {})
            add_capabilities = capabilities.get('add', [])
            if add_capabilities:
                cmd += ['--cap-add=%s' % ','.join(add_capabilities)]

        # Privileged
        privileged = security_context.get('privileged', False)
        if privileged:
            cmd += ['--privileged']
            cmd += ['-v', '/data/inner/docker:/var/lib/docker']

        cmd += [image_name]

        if self.job['definition'].get('command', None):
            cmd += self.job['definition']['command']

        try:
            c.header("Run container", show=True)
            c.execute(cmd, show=True, show_cmd=False)
            c.execute(("docker", "commit", container_name, image_name))
        except Exception as e:
            try:
                # Find out if container was killed due to oom
                out = subprocess.check_output(['docker', 'inspect', container_name,
                                               '-f', '{{.State.OOMKilled}}']).strip()
            except Exception as ex:
                logger.exception(ex)
                raise Failure("Could not get OOMKilled state of container")

            if out == 'true':
                raise Failure('Container was killed, because it ran out of memory')

            try:
                exit_code = subprocess.check_output(['docker', 'inspect', container_name,
                                                     '-f', '{{.State.ExitCode}}']).strip()
            except Exception as ex:
                logger.exception(ex)
                raise Failure("Could not get exit code of container")

            try:
                c.execute(("docker", "commit", container_name, image_name))
                c.header("Finalize", show=True)
                self.push_container(image_name)
            except Exception as ex:
                logger.exception(ex)
                raise Failure("Could not commit and push container")

            logger.exception(e)
            raise Failure("Container run exited with error (exit code=%s)" % exit_code)

        finally:
            try:
                collector.stop()
                self.post_stats(collector.get_result())
                c.execute(("docker", "rm", container_name))
            except:
                pass


    def build_docker_container(self, image_name, cache_image):
        c = self.console

        self._login_source_registries()

        try:
            c.header("Build image", show=True)
            self.get_cached_image(cache_image)
            docker_file = os.path.normpath(os.path.join(self._get_build_context_current_job(),
                                                        self.job['dockerfile']))

            cmd = ['docker', 'build',
                   '--cache-from', cache_image,
                   '-t', image_name,
                   '-f', docker_file,
                   '.']

            if 'build_arguments' in self.job and self.job['build_arguments']:
                for name, value in self.job['build_arguments'].iteritems():
                    cmd += ['--build-arg', '%s=%s' % (name, value)]

            cmd += ['--build-arg', 'INFRABOX_BUILD_NUMBER=%s' % self.build['build_number']]

            cwd = self._get_build_context_current_job()
            c.execute(cmd, cwd=cwd, show=True)
            self.cache_docker_image(image_name, cache_image)
        except Exception as e:
            raise Failure("Failed to build the image: %s" % e)

        self._logout_source_registries()

    def run_job_docker_image(self, c):
        image_name = self.job['definition']['image'].replace('$INFRABOX_BUILD_NUMBER', str(self.build['build_number']))

        self._login_source_registries()
        self.run_docker_container(image_name)
        self._logout_source_registries()

        self.deploy_container(image_name)

        c.header("Finalize", show=True)
        self.push_container(image_name)

    def _login_registry(self, reg):
        c = self.console

        try:
            if reg['type'] == 'ecr':
                login_env = {
                    'AWS_ACCESS_KEY_ID': reg['access_key_id'],
                    'AWS_SECRET_ACCESS_KEY': reg['secret_access_key'],
                    'AWS_DEFAULT_REGION': reg['region'],
                    'PATH': os.environ['PATH']
                }

                c.execute(['/usr/local/bin/ecr_login.sh'], show=True, env=login_env)
            elif reg['type'] == 'gcr':
                with open('/tmp/gcr_sa.json', 'w+') as sa:
                    sa.write(reg['service_account'])

                c.execute(['gcloud', 'auth', 'activate-service-account', '--key-file', '/tmp/gcr_sa.json'], show=True)
                c.execute(['gcloud', 'docker', '-a'], show=True)
            elif reg['type'] == 'docker-registry' and 'username' in reg:
                cmd = ['docker', 'login', '-u', reg['username'], '-p', reg['password']]

                host = reg['host']
                if not host.startswith('docker.io') and not host.startswith('index.docker.io'):
                    cmd += [host]

                c.execute(cmd, show=False)
        except Exception as e:
            raise Failure("Failed to login to registry: " + e.message)

    def _logout_registry(self, reg):
        c = self.console
        c.execute(['docker', 'logout', reg['host']], show=False)

    def _login_source_registries(self):
        for r in self.registries:
            self._login_registry(r)

    def _logout_source_registries(self):
        for r in self.registries:
            self._logout_registry(r)

    def run_job_docker(self, c):
        self._login_source_registries()

        image_name = get_registry_name() + '/' \
                     + self.project['id'] + '/' \
                     + self.job['name']
        image_name_build = image_name + ':build_%s' % self.build['build_number']
        image_name_latest = image_name + ':latest'

        self.build_docker_container(image_name_build, image_name_latest)

        if not self.job['build_only']:
            self.run_docker_container(image_name_build)

        self.deploy_container(image_name_build)

        c.header("Finalize", show=True)
        self.push_container(image_name_build)

    def get_cached_image(self, image_name_latest):
        c = self.console

        if not self.job['definition'].get('cache', {}).get('image', False):
            c.collect("Not pulling cached image, because cache.image has been set to false", show=True)
            return

        c.collect("Get cached image %s" % image_name_latest, show=True)

        self.login_docker_registry()
        c.execute(['docker', 'pull', image_name_latest], show=True, ignore_error=True)
        self.logout_docker_registry()

    def cache_docker_image(self, image_name_build, image_name_latest):
        c = self.console

        if not self.job['definition'].get('cache', {}).get('image', False):
            c.collect("Not pushed cached image, because cache.image has been set to false", show=True)
            return

        c.collect("Upload cached image %s" % image_name_latest, show=True)

        try:
            self.login_docker_registry()
            c.execute(['docker', 'tag', image_name_build, image_name_latest], show=True)
            c.execute(['docker', 'push', image_name_latest], show=True)
        except:
            c.collect("Failed to upload cache image: %s" % image_name_build, show=True)
            c.execute(['docker', 'images'], show=True)
        finally:
            self.logout_docker_registry()

    def parse_infrabox_json(self, path):
        with open(path, 'r') as f:
            data = None
            try:
                data = json.load(f)
                self.console.collect(json.dumps(data, indent=4), show=True)
                validate_json(data)
            except Exception as e:
                raise Failure(e.__str__())

            return data

    def check_file_exist(self, data, infrabox_context):
        jobs = data.get('jobs', [])
        for job in jobs:
            job_type = job['type']

            if job_type == "docker-compose":
                composefile = job['docker_compose_file']
                p = os.path.join(infrabox_context, composefile)
                if not os.path.exists(p):
                    return # might be dynamically generated

                # validate it
                try:
                    create_from(p)
                except Exception as e:
                    raise Failure("%s: %s" % (p, e.message))

            if job_type == "workflow":
                workflowfile = job['infrabox_file']
                p = os.path.join(infrabox_context, workflowfile)
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
                     infrabox_context=None, infrabox_paths=None):
        #pylint: disable=too-many-locals

        if not infrabox_context:
            infrabox_context = self.mount_repo_dir

        if not infrabox_paths:
            infrabox_paths = {}

        self.rewrite_depends_on(data)

        jobs = []
        for job in data['jobs']:
            job['id'] = str(uuid.uuid4())
            job['avg_duration'] = 0
            job['repo'] = repo
            job['infrabox_context'] = os.path.normpath(infrabox_context)

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
                clone_url = job['clone_url']

                sub_path = os.path.join('.infrabox', 'tmp', job_name)
                new_repo_path = os.path.join(self.mount_repo_dir, sub_path)
                c.execute(['rm', '-rf', new_repo_path])
                os.makedirs(new_repo_path)

                self.clone_repo(job['commit'], clone_url, None, None, True, sub_path)

                c.header("Parsing infrabox.json", show=True)
                ib_file = job.get('infrabox_file', 'infrabox.json')
                ib_path = os.path.join(new_repo_path, ib_file)

                if ib_path in infrabox_paths:
                    raise Failure("Recursive include detected")

                infrabox_paths[ib_path] = True
                c.collect("file: %s" % ib_path)
                yml = self.parse_infrabox_json(ib_path)

                git_repo = {
                    "clone_url": job['clone_url'],
                    "commit": job['commit'],
                    "infrabox_file": ib_file,
                    "clone_all": True
                }

                new_infrabox_context = os.path.dirname(ib_path)

                self.check_file_exist(yml, new_infrabox_context)
                sub = self.get_job_list(yml, c, git_repo,
                                        parent_name=job_name,
                                        infrabox_context=new_infrabox_context,
                                        infrabox_paths=infrabox_paths)

                for s in sub:
                    s['infrabox_context'] = s['infrabox_context'].replace(new_repo_path, self.mount_repo_dir)

                del infrabox_paths[ib_path]

            if job['type'] == 'workflow':
                c.header("Parsing infrabox.json", show=True)
                p = os.path.join(infrabox_context, job['infrabox_file'])
                c.collect("file: %s\n" % p)

                if p in infrabox_paths:
                    raise Failure("Recursive include detected")

                infrabox_paths[p] = True

                yml = self.parse_infrabox_json(p)
                new_infrabox_context = os.path.dirname(p)
                self.check_file_exist(yml, new_infrabox_context)

                sub = self.get_job_list(yml, c, repo,
                                        parent_name=job_name,
                                        infrabox_context=new_infrabox_context)

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
    get_env('INFRABOX_ROOT_URL')
    get_env('INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES')
    get_env('INFRABOX_LOCAL_CACHE_ENABLED')
    get_env('INFRABOX_JOB_MAX_OUTPUT_SIZE')
    console = ApiConsole()

    j = None
    try:
        j = RunJob(console)
        j.main()
        j.console.header('Finished', show=True)
        j.console.flush()

        with open('/dev/termination-log', 'w+') as out:
            out.write('Job finished successfully')

    except Failure as e:
        j.console.header('Failure', show=True)
        j.console.collect(e.message, show=True)
        j.console.flush()

        with open('/dev/termination-log', 'w+') as out:
            out.write(e.message)

        sys.exit(1)
    except:
        print_stackdriver()
        if j:
            j.console.header('An error occured', show=True)
            msg = traceback.format_exc()
            j.console.collect(msg, show=True)
            j.console.flush()

            with open('/dev/termination-log', 'w+') as out:
                out.write(msg)

            sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except:
        print_stackdriver()
        sys.exit(1)
