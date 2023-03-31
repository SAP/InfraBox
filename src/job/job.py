#!/usr/bin/python3
#pylint: disable=too-many-lines,attribute-defined-outside-init,too-many-public-methods,too-many-locals
import sys

import os
import shutil
import time
import json
import subprocess
import re
import uuid
import base64
import traceback
import urllib3
import yaml
import tarfile
import signal

from pyinfrabox.infrabox import validate_json
from pyinfrabox.docker_compose import create_from

from infrabox_job.stats import StatsCollector
from infrabox_job.process import ApiConsole, Failure, Error
from infrabox_job.job import Job
from infrabox_job import find_infrabox_file

from pyinfraboxutils.testresult import Parser as TestresultParser
from pyinfraboxutils.coverage import Parser as CoverageParser
from pyinfraboxutils import get_env
from pyinfraboxutils import get_logger

urllib3.disable_warnings()
logger = get_logger('scheduler')

ERR_EXIT_FAILURE = 1
ERR_EXIT_ERROR = 2

BUILD_ARGS = ('GITHUB_OAUTH_TOKEN', 'GITHUB_BASE_URL')

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
        self.storage_dir = '/data/tmp/storage'
        self.error = None

        if os.path.exists(self.storage_dir):
            shutil.rmtree(self.storage_dir)

        os.makedirs(self.storage_dir)

        self.mount_repo_dir = '/data/repo'
        self.mount_data_dir = self.mount_repo_dir + '/.infrabox'

    def create_infrabox_directories(self):
        if os.path.exists(self.mount_data_dir):
            shutil.rmtree(self.mount_data_dir, ignore_errors=True)

        #
        # /data/tmp/infrabox is mounted to the same path on the host
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

        # <data_dir>/shared is mounted in the job to /infrabox/shared for docker_compose jobs
        self.infrabox_shared_dir = os.path.join(self.mount_data_dir, 'shared')
        makedirs(self.infrabox_shared_dir)

        # <data_dir>/upload/testresult is mounted in the job to /infrabox/upload/testresult
        self.infrabox_testresult_dir = os.path.join(self.infrabox_upload_dir, 'testresult')
        makedirs(self.infrabox_testresult_dir)

        # <data_dir>/upload/coverage is mounted in the job to /infrabox/upload/coverage
        self.infrabox_coverage_dir = os.path.join(self.infrabox_upload_dir, 'coverage')
        makedirs(self.infrabox_coverage_dir)

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
                    "url": self.env_vars['INFRABOX_BUILD_URL']
                }
            }

            if self.project['type'] == 'github':
                o['commit'] = {}
                o['commit']["branch"] = self.commit['branch']
                o['commit']["id"] = self.commit['id']

            json.dump(o, out)

    def compress(self, source, output):
        cmd = "tar -cf - --directory %s . | pv -L 500m | python3 -m snappy -c - %s" % (source, output)
        self.console.execute(cmd, cwd=source, show=True, shell=True, show_cmd=False)

    def uncompress(self, source, output):
        cmd = "python3 -m snappy -d %s - | tar -xf - -C %s" % (source, output)
        self.console.execute(cmd, cwd=output, show=True, shell=True, show_cmd=False)

    def get_files_in_dir(self, d, ending=None):
        result = []
        for root, _, files in os.walk(d):
            for f in files:
                if ending:
                    if not f.endswith(ending):
                        continue

                result.append(os.path.join(root, f))

        return result

    def clone_repo(self, commit, clone_url, branch, ref, full_history, sub_path=None, submodules=True, token=None):
        c = self.console
        mount_repo_dir = self.mount_repo_dir

        if sub_path:
            mount_repo_dir = os.path.join(mount_repo_dir, sub_path)

        if os.environ['INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES'] == 'true':
            c.execute(('git', 'config', '--global', 'http.sslVerify', 'false'), show=True)

        if token and clone_url.startswith("http"):
            schema, url = clone_url.split("://")
            clone_url = schema + "://" + token + '@' + url

        cmd = ['git', 'clone']

        if not full_history:
            cmd += ['--depth=10']

            if branch:
                cmd += ['--single-branch', '-b', branch]

        cmd += [clone_url, mount_repo_dir]
        c.execute_mask(cmd, show=True, retry=True, mask=token)

        if ref:
            cmd = ['git', 'fetch']

            if not full_history:
                cmd += ['--depth=10']

            cmd += [clone_url, ref]
            c.execute_mask(cmd, cwd=mount_repo_dir, show=True, retry=True, mask=token)

        c.execute_mask(['git', 'config', 'remote.origin.url', clone_url], cwd=mount_repo_dir, show=True, mask=token)
        c.execute(['git', 'config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*'],
                  cwd=mount_repo_dir, show=True)
        try:
            c.execute(['git', 'fetch', 'origin', commit], cwd=mount_repo_dir, show=True, retry=False)
        except Exception:
            c.collect("failed fetching commit: %s, trying to fetch full history and retry" % commit)
            c.execute(['git', 'fetch'], cwd=mount_repo_dir, show=True, retry=True)
            c.execute(['git', 'fetch', 'origin', commit], cwd=mount_repo_dir, show=True, retry=True)

        cmd = ['git', 'checkout', '-qf', commit]

        c.execute(cmd, cwd=mount_repo_dir, show=True)

        if submodules:
            c.execute(['git', 'submodule', 'init', '-q'], cwd=mount_repo_dir, show=True, retry=True)
            c.execute(['git', 'submodule', 'update', '-q'], cwd=mount_repo_dir, show=True, retry=True)


    def get_source(self):
        c = self.console

        if self.job['repo']:
            repo = self.job['repo']
            clone_url = repo['clone_url']
            branch = repo.get('branch', None)
            ref = repo.get('ref', None)

            definition = self.job['definition']

            if not definition:
                definition = {}

            def_repo = definition.get('repository', {})
            repo_clone = def_repo.get('clone', True)
            repo_submodules = def_repo.get('submodules', True)
            full_history = def_repo.get('full_history', None)
            github_token = def_repo.get('github_api_token', None)
            if not github_token:
                github_token = self.repository.get('github_api_token', None)
            if full_history is None:
                full_history = repo.get('full_history', False)

            commit = repo['commit']

            if not repo_clone:
                return

            self.clone_repo(commit, clone_url, branch, ref, full_history, submodules=repo_submodules, token=github_token)
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
        c.execute(['ls', '-alh', self.mount_repo_dir], show=True)

    def main_create_jobs(self):
        c = self.console

        ib_file = self.job['definition'].get('infrabox_file')

        if not ib_file:
            ib_file = find_infrabox_file(self.mount_repo_dir)
        else:
            ib_file = os.path.join(self.mount_repo_dir, ib_file)

        if not ib_file:
            raise Error("infrabox file not found")

        c.header("Parsing infrabox file: %s" % ib_file, show=True)
        data = self.parse_infrabox_file(ib_file)
        self.check_file_exist(data, self.mount_repo_dir)

        c.header("Creating jobs", show=True)
        jobs = self.get_job_list(data, c, self.job['repo'], infrabox_paths={ib_file: True})

        if jobs:
            self.create_jobs(jobs)
            c.collect("Done creating jobs")
        else:
            c.collect("No jobs")

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

    def config_github(self):
        if os.environ.get('INFRABOX_GITHUB_ENABLED') == "false":
            self.console.collect("Github not enabled", show=True)
            return
        if not self.enable_token_access:
            self.console.collect("Github token not configured", show=True)
        token = self.repository.get('github_api_token', None)
        github_url = "https://" + self.github_host

        if token:
            self.console.collect("GITHUB_OAUTH_TOKEN=********", show=True)
            github_url = "https://" + token + '@' + self.github_host
            self.console.collect("GITHUB_BASE_URL=" + github_url.replace(token, '********'), show=True)
        else:
            self.console.collect("GITHUB_BASE_URL=" + github_url, show=True)

        cmd = ["git", "config", "--global", 'url."' + github_url + '".insteadOf', '"https://' + self.github_host + '"']
        if token:
            self.console.execute_mask(cmd, show=True, mask=token)
            self.environment['GITHUB_OAUTH_TOKEN'] = token

        self.environment['GITHUB_BASE_URL'] = github_url

    def main(self):
        self.load_data()
        # Date
        self.console.collect("Date:", show=True)
        self.console.execute(['date'], show=True, show_cmd=False)

        # Show environment
        self.console.collect("Environment:", show=True)
        for name, value in self.env_vars.items():
            self.console.collect("%s=%s" % (name, value), show=True)

        self.console.collect("", show=True)

        # Show secrets
        if self.secrets:
            self.console.collect("Secrets:", show=True)
            for name, _ in self.secrets.items():
                self.console.collect("%s=*****" % name, show=True)
            self.console.collect("", show=True)

        # Show Registries
        if self.registries:
            self.console.collect("Registries:", show=True)
            for r in self.registries:
                self.console.collect("%s" % r['host'], show=True)
            self.console.collect("", show=True)

        # Show Deployments
        if self.deployments:
            self.console.collect("Deployments:", show=True)
            for d in self.deployments:
                tag = d.get('tag', 'build_%s' % self.build['build_number'])
                v = "%s/%s:%s" % (d['host'], d['repository'], tag)
                self.console.collect(v, show=True)
            self.console.collect("", show=True)

        self.config_github()
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
        archive_exists = False
        testresult_exists = False

        if os.path.exists(self.infrabox_archive_dir):
            files = self.get_files_in_dir(self.infrabox_archive_dir)

            if files:
                c.collect("Uploading /infrabox/upload/archive", show=True)
                archive_exists = True
                for f in files:
                    c.collect("%s" % f, show=True)
                    self.post_file_to_api_server("/archive", f, filename=f.replace(self.infrabox_upload_dir+'/', ''))

        if os.path.exists(self.infrabox_testresult_dir):
            files = self.get_files_in_dir(self.infrabox_testresult_dir)

            if files:
                testresult_exists = True
                for f in files:
                    c.collect("%s" % f, show=True)

        tar_file = os.path.join(self.infrabox_upload_dir, 'all_archives' + '.tar.gz')
        with tarfile.open(tar_file, mode='w:gz') as archive:
            if archive_exists:
                archive.add(self.infrabox_archive_dir, arcname='archive')
            if testresult_exists:
                archive.add(self.infrabox_testresult_dir, arcname='testresult')

        self.post_file_to_api_server("/archive", tar_file)


    def upload_coverage_results(self):
        if not os.path.exists(self.infrabox_coverage_dir):
            return

        files = self.get_files_in_dir(self.infrabox_coverage_dir, ending=".xml")
        if not files:
            return

        converted_result = self.convert_coverage_result(self.infrabox_coverage_dir)
        mu_path = os.path.join(self.infrabox_markup_dir, 'coverage.json')

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
            c.collect("%s" % f, show=True)
            self.post_file_to_api_server("/archive", f, filename=f.replace(self.infrabox_upload_dir+'/', ''))

            try:
                converted_result = self.convert_test_result(f)
                self.post_file_to_api_server("/testresult", converted_result, filename='data')
            except Exception as e:
                self.console.collect("Failed to parse test result: %s" % e, show=True)

    def upload_markup_files(self):
        c = self.console
        if not os.path.exists(self.infrabox_markup_dir):
            return

        files = self.get_files_in_dir(self.infrabox_markup_dir, ending=".json")
        for f in files:
            c.collect("%s" % f, show=True)

            file_name = os.path.basename(f)
            self.post_file_to_api_server("/markup", f, filename=file_name)

    def upload_badge_files(self):
        c = self.console
        if not os.path.exists(self.infrabox_badge_dir):
            return

        files = self.get_files_in_dir(self.infrabox_badge_dir, ending=".json")

        for f in files:
            c.collect("%s" % f, show=True)

            file_name = os.path.basename(f)
            self.post_file_to_api_server("/badge", f, filename=file_name)

    def create_dynamic_jobs(self):
        c = self.console

        ib_file = find_infrabox_file(self.infrabox_output_dir)

        if ib_file:
            infrabox_context = os.path.dirname(ib_file)
            c.header("Creating jobs", show=True)
            data = self.parse_infrabox_file(ib_file)
            self.check_file_exist(data, infrabox_context)
            jobs = self.get_job_list(data, c, self.job['repo'],
                                     infrabox_paths={ib_file: True},
                                     infrabox_context=infrabox_context)
            c.collect(json.dumps(jobs, indent=4), show=True)

            if jobs:
                self.create_jobs(jobs)
                c.collect("Done creating jobs")
            else:
                c.collect("No jobs")

    def _get_size(self, start_path):
        total_size = 0
        for dirpath, _, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    def finalize_upload(self):
        self.upload_coverage_results()
        self.upload_test_results()
        self.upload_markup_files()
        self.upload_badge_files()
        self.upload_archive()

    def handle_abort(self, signum, sigframe):
        if not self.aborted:
            self.aborted = True
            self.console.collect("##Aborted", show=True)
            self.finalize_upload()

    def main_run_job(self):
        c = self.console
        self.create_jobs_json()

        signal.signal(signal.SIGTERM, self.handle_abort)

        # base dir for inputs
        storage_inputs_dir = os.path.join(self.storage_dir, 'inputs')

        # Sync deps
        c.collect("Syncing inputs:", show=True)
        for dep in self.parents:
            storage_input_file_dir = os.path.join(storage_inputs_dir, dep['id'])
            os.makedirs(storage_input_file_dir)

            # Get files.json
            storage_input_file_tar = os.path.join(storage_input_file_dir, 'output.tar.snappy')
            self.get_file_from_api_server('/output/%s' % dep['id'], storage_input_file_tar, split=True)

            if os.path.isfile(storage_input_file_tar):
                c.collect("output found for %s" % dep['name'], show=True)
                dir_name = dep['name'].split('/')[-1]

                m = re.search('(.*)\.([0-9]+)', dir_name)
                if m:
                    dir_name = m.group(1)

                infrabox_input_dir = os.path.join(self.infrabox_inputs_dir, dir_name)
                os.makedirs(infrabox_input_dir)
                self.uncompress(storage_input_file_tar, infrabox_input_dir)
                c.execute(['ls', '-alh', infrabox_input_dir], show=True)
                os.remove(storage_input_file_tar)
            else:
                c.collect("no output found for %s" % dep['name'], show=True)
        c.collect("", show=True)

        # <storage_dir>/cache is synced with the corresponding
        # Storage path which stores the compressed cache
        storage_cache_dir = os.path.join(self.storage_dir, 'cache')
        os.makedirs(storage_cache_dir)

        storage_cache_tar = os.path.join(storage_cache_dir, 'cache.tar.snappy')

        c.collect("Syncing cache:", show=True)
        if not self.job['definition'].get('cache', {}).get('data', True):
            c.collect("Not downloading cache, because cache.data has been set to false", show=True)
        else:
            self.get_file_from_api_server("/cache", storage_cache_tar, split=True)

            if os.path.isfile(storage_cache_tar):
                c.collect("Unpacking cache", show=True)
                try:
                    self.uncompress(storage_cache_tar, self.infrabox_cache_dir)
                except:
                    c.collect("Failed to unpack cache", show=True)
                os.remove(storage_cache_tar)
            else:
                c.collect("no cache found", show=True)
        c.collect("", show=True)

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
            if self.aborted:
                return
            self.finalize_upload()

            # Compressing output
            c.collect("Uploading /infrabox/output", show=True)
            if os.path.isdir(self.infrabox_output_dir) and os.listdir(self.infrabox_output_dir):
                storage_output_dir = os.path.join(self.storage_dir, self.job['id'])
                os.makedirs(storage_output_dir)

                storage_output_tar = os.path.join(storage_output_dir, 'output.tar.snappy')
                self.compress(self.infrabox_output_dir, storage_output_tar)
                file_size = os.stat(storage_output_tar).st_size

                c.collect("Output size: %s kb" % (file_size / 1024), show=True)
                self.post_file_to_api_server("/output", storage_output_tar, split=True)
            else:
                c.collect("Output is empty", show=True)

            c.collect("", show=True)

        self.create_dynamic_jobs()

        # Compressing cache
        c.collect("Uploading /infrabox/cache", show=True)
        if not self.job['definition'].get('cache', {}).get('data', True):
            c.collect("Not updating cache, because cache.data has been set to false", show=True)
        else:
            if os.path.isdir(self.infrabox_cache_dir) and os.listdir(self.infrabox_cache_dir):
                self.compress(self.infrabox_cache_dir, storage_cache_tar)

                file_size = os.stat(storage_cache_tar).st_size

                c.collect("Output size: %s kb" % (file_size / 1024), show=True)
                self.post_file_to_api_server('/cache', storage_cache_tar, split=True)
            else:
                c.collect("Cache is empty", show=True)
        c.collect("", show=True)

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

            service_markup_dir = os.path.join(self.infrabox_markup_dir, service)
            makedirs(service_markup_dir)

            service_badge_dir = os.path.join(self.infrabox_badge_dir, service)
            makedirs(service_badge_dir)

            service_archive_dir = os.path.join(self.infrabox_archive_dir, service)
            makedirs(service_archive_dir)

            service_volumes = [
                "%s:/infrabox/cache" % service_cache_dir,
                "%s:/infrabox/inputs" % self.infrabox_inputs_dir,
                "%s:/infrabox/output" % service_output_dir,
                "%s:/infrabox/upload/testresult" % service_testresult_dir,
                "%s:/infrabox/upload/markup" % service_markup_dir,
                "%s:/infrabox/upload/badge" % service_badge_dir,
                "%s:/infrabox/upload/coverage" % service_coverage_dir,
                "%s:/infrabox/upload/archive" % service_archive_dir,
                "%s:/infrabox/shared" % self.infrabox_shared_dir,
            ]

            for v in compose_file_content['services'][service].get('volumes', []):
                if isinstance(v, str):
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
                else:
                    service_volumes += ['%s:/infrabox/context' % self.mount_repo_dir]
            else:
                service_volumes += ['%s:/infrabox/context' % self.mount_repo_dir]

            if os.environ['INFRABOX_LOCAL_CACHE_ENABLED'] == 'true':
                service_volumes.append("/local-cache:/infrabox/local-cache")

            compose_file_content['services'][service]['volumes'] = service_volumes

            image_name = get_registry_name() + '/' \
                         + self.project['id'] + '/' \
                         + self.job['name'] + '/' \
                         + service

            image_name_latest = image_name + ':latest'
            build = compose_file_content['services'][service].get('build', None)
            image = compose_file_content['services'][service].get('image', None)

            if build:
                if not image:
                    compose_file_content['services'][service]['image'] = image_name_latest

                build['cache_from'] = [image_name_latest]
                self.get_cached_image(image_name_latest)

                build['args'] = build.get('args', [])
                build['args'] += ['INFRABOX_BUILD_NUMBER=%s' % self.build['build_number']]
                for arg in BUILD_ARGS:
                    if self.environment.get(arg, None):
                        build['args'] += ['%s=%s' % (arg, self.environment[arg])]


        with open(compose_file_new, "w+") as out:
            json.dump(compose_file_content, out)

        collector = StatsCollector()

        self._login_source_registries()

        try:
            try:
                c.execute(['docker-compose', '-f', compose_file_new, 'rm'],
                          env=self.environment)
            except Exception as e:
                logger.exception(e)

            stop_timeout = self.job['definition'].get('stop_timeout', '10')
            parallel_build = self.job['definition'].get('parallel_build', False)
            compose_profiles = self.job['definition'].get('compose_profiles', [])
            self.environment['PATH'] = os.environ['PATH']
            self.environment['DOCKER_BUILDKIT'] = '0'
            self.environment['COMPOSE_DOCKER_CLI_BUILD'] = '0'
            if self.job['definition'].get('enable_docker_build_kit', False) is True:
                c.collect('BUILDKIT is enabled during build!', show=True)
                self.environment['DOCKER_BUILDKIT'] = '1'
                self.environment['COMPOSE_DOCKER_CLI_BUILD']= '1'


            cmds = ['docker-compose', '-f', compose_file_new, 'build']

            if parallel_build:
                cmds.append('--parallel')

            c.execute_mask(cmds,show=True, env=self.environment, mask=self.repository.get('github_api_token', None))

            c.header("Run docker-compose", show=True)

            cwd = self._get_build_context_current_job()
            cmds = ['docker-compose']
            if compose_profiles:
                for f in compose_profiles:
                    cmds.append('--profile')
                    cmds.append(f)
            cmds += ['-f', compose_file_new, 'up', '--abort-on-container-exit', '--timeout', str(stop_timeout)]
            c.execute(cmds, env=self.environment, show=True, cwd=cwd)
        except:
            raise Failure("Failed to build and run container")
        finally:
            c.header("Finalize", show=True)
            try:
                collector.stop()
                self.post_stats(collector.get_result())
                c.execute(['docker-compose', '-f', compose_file_new, 'rm', '--force'],
                          env=self.environment)
            except Exception as e:
                logger.exception(e)

        self._logout_source_registries()

        for service in compose_file_content['services']:
            image_name = get_registry_name() + '/' \
                         + self.project['id'] + '/' \
                         + self.job['name'] + '/' \
                         + service

            image_name_latest = image_name + ':latest'
            build = compose_file_content['services'][service].get('build', None)

            if build:
                image = compose_file_content['services'][service]['image']
                self.cache_docker_image(image, image_name_latest)

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
            raise Error('Invalid build_context: %s' % build_context)

        return os.path.normpath(build_context)

    def deploy_image(self, image_name, dep):
        c = self.console
        tag = dep.get('tag', 'build_%s' % self.build['build_number'])
        dep_image_name = dep['host'] + '/' + dep['repository'] + ":" + tag
        c.execute(['docker', 'tag', image_name, dep_image_name], show=True)

        self._login_registry(dep)
        c.execute(['docker', 'push', dep_image_name], show=True)
        self._logout_registry(dep)


    def deploy_images(self, image_name):
        c = self.console
        if not self.deployments:
            return
        header = False

        for dep in self.deployments:
            if dep.get('target', None):
                continue
            if dep.get("always_push", False) or not self.error:
                if not header:
                    c.header("Deploying", show=True)
                    header = True
                self.deploy_image(image_name, dep)

    def login_docker_registry(self):
        c = self.console
        c.execute(['docker', 'login',
                   '-u', 'infrabox',
                   '-p', os.environ['INFRABOX_JOB_TOKEN'],
                   get_registry_name()], show=False)

    def logout_docker_registry(self):
        c = self.console
        c.execute(['docker', 'logout', get_registry_name()], show=False)

    def run_docker_pull(self, image_name):
        c = self.console
        cmd = ['docker', 'pull', image_name]
        c.execute(cmd, show=True, show_cmd=False)

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
        for name, value in self.environment.items():
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

        # Privileged
        security_context = self.job['definition'].get('security_context', {})
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

            if self.job['definition'].get('cache', {}).get('image', False) or self.job['definition'].get('deployments', None):
                c.execute(("docker", "commit", container_name, image_name))
        except Exception as e:
            try:
                # Find out if container build was failed
                out = subprocess.check_output(['docker', 'images', '-q', image_name]).strip()
                if not out:
                    raise Failure("Error running container")
            except Exception as ex:
                logger.exception(ex)
                raise Failure("Error running container")
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

            c.print_failure("Container run exited with error (exit code=%s)" % exit_code)
            c.header("Error", show=True)
            logger.exception(e)
            raise Failure("Container run exited with error (exit code=%s)" % exit_code)

        finally:
            try:
                collector.stop()
                self.post_stats(collector.get_result())
                c.execute(("docker", "rm", container_name))
            except:
                pass


    def build_docker_image(self, image_name, cache_image, target=None):
        c = self.console

        self._login_source_registries()

        try:
            c.header("Build image", show=True)
            cache_from = self.get_cached_image(cache_image)
            docker_file = os.path.normpath(os.path.join(self._get_build_context_current_job(),
                                                        self.job['dockerfile']))

            cmd = ['docker', 'build',
                   '-t', image_name,
                   '-f', docker_file,
                   '.']

            # Memory limit
            memory_limit = os.environ['INFRABOX_JOB_RESOURCES_LIMITS_MEMORY']
            cmd += ['-m', '%sm' % memory_limit]

            # Labels
            cmd += ['--label', 'net.infrabox.job.id=%s' % self.job['id']]

            # Build args
            cmd += ['--build-arg', 'INFRABOX_BUILD_NUMBER=%s' % self.build['build_number']]

            if 'build_arguments' in self.job and self.job['build_arguments']:
                for name, value in self.job['build_arguments'].items():
                    cmd += ['--build-arg', '%s=%s' % (name, value)]

            for arg in BUILD_ARGS:
                if self.environment.get(arg, None):
                    cmd += ['--build-arg', '%s=%s' % (arg, self.environment[arg])]

            if target:
                cmd += ['--target', target]
            elif cache_from:
                cmd += ['--cache-from', cache_image]

            cwd = self._get_build_context_current_job()

            if  self.job['definition'].get('enable_docker_build_kit', False) is True:
                os.environ['DOCKER_BUILDKIT'] = '1'

            c.execute_mask(cmd, cwd=cwd, show=True, mask=self.repository.get('github_api_token', None))
            self.cache_docker_image(image_name, cache_image)

        except Exception as e:
            raise Error("Failed to build the image: %s" % e)

        self._logout_source_registries()

    def run_job_docker_image(self, c):
        image_name = self.job['definition']['image'].replace('$INFRABOX_BUILD_NUMBER', str(self.build['build_number']))

        try:
            if self.job.get('definition', {}).get('run', True):
                self._login_source_registries()
                self.run_docker_container(image_name)
                self._logout_source_registries()
            else:
                self._login_source_registries()
                self.run_docker_pull(image_name)
                self._logout_source_registries()
        except Exception as e:
            self.error = e

        self.deploy_images(image_name)
        if self.error:
            raise self.error
        c.header("Finalize", show=True)

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
                c.execute(['gcloud', 'auth', 'configure-docker'], show=True)
            elif reg['type'] == 'docker-registry' and 'username' in reg:
                cmd = ['docker', 'login', '-u', reg['username'], '-p', reg['password']]

                host = reg['host']
                if not host.startswith('docker.io') and not host.startswith('index.docker.io'):
                    cmd += [host]

                c.execute(cmd, show=False)
        except Exception as e:
            raise Error("Failed to login to registry: " + e.message)

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

        if self.deployments:
            for d in self.deployments:
                target = d.get('target', None)

                if not target:
                    continue

                self.build_docker_image(image_name_build, image_name_latest, target=target)
                c.header("Deploying", show=True)
                self.deploy_image(image_name_build, d)

        target = self.job['definition'].get('target', None)
        self.build_docker_image(image_name_build, image_name_latest, target=target)

        try:
            if not self.job.get('build_only', True):
                self.run_docker_container(image_name_build)
        except Exception as e:
            self.error = e

        self.deploy_images(image_name_build)

        c.header("Finalize", show=True)
        if self.error:
            raise self.error



    def get_cached_image(self, image_name_latest):
        c = self.console

        if not self.job['definition'].get('cache', {}).get('image', False):
            c.collect("Not pulling cached image, because cache.image has been set to false", show=True)
            return False

        c.collect("Get cached image %s" % image_name_latest, show=True)

        self.login_docker_registry()
        c.execute(['docker', 'pull', image_name_latest], show=True, ignore_error=True)
        self.logout_docker_registry()
        return True

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

    def parse_infrabox_file(self, path):
        with open(path, 'r') as f:
            data = None
            try:
                data = json.load(f)
                self.console.collect(json.dumps(data, indent=4), show=True)
            except ValueError:
                f.seek(0)
                data = yaml.load(f)
                self.console.collect(yaml.dump(data, default_flow_style=False), show=True)
            try:
                validate_json(data)
            except Exception as e:
                raise Error(e.__str__())

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
                    raise Error("%s: %s" % (p, e.message))

            if job_type == "workflow":
                workflowfile = job['infrabox_file']
                p = os.path.join(infrabox_context, workflowfile)
                if not os.path.exists(p):
                    raise Error("%s does not exist" % p)

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
                        d['on'] = ["finished", "error", "failure", "skipped", "killed", "unstable"]
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

            if job.get('repo', None):
                job['repo'].update(repo)
            else:
                job['repo'] = repo

            job['infrabox_context'] = os.path.normpath(infrabox_context)

            if parent_name != '':
                job['name'] = parent_name + "/" + job['name']

                deps = job.get('depends_on', [])
                for x in range(0, len(deps)):
                    deps[x]['job'] = parent_name + "/" + deps[x]['job']

            job_name = job['name']
            if job['type'] != "workflow" and job['type'] != "git":
                jobs.append(job)
                continue

            if job['type'] == "git":
                c.header("Clone repo %s" % job['clone_url'], show=True)
                clone_url = job['clone_url']
                branch = job.get("branch", None)

                sub_path = os.path.join('.infrabox', 'tmp', job_name)
                new_repo_path = os.path.join(self.mount_repo_dir, sub_path)
                c.execute(['rm', '-rf', new_repo_path])
                os.makedirs(new_repo_path)

                github_token = None
                if job.get('repo', None):
                    try:
                        github_token = job['repo'].get('github_api_token', None)
                    except:
                        pass

                if not github_token:
                    github_token = self.repository.get('github_api_token', None)

                self.clone_repo(job['commit'], clone_url, branch, None, True, sub_path, token=github_token)

                c.header("Parsing infrabox file", show=True)
                ib_file = job.get('infrabox_file', None)
                if not ib_file:
                    ib_path = find_infrabox_file(new_repo_path)
                else:
                    ib_path = os.path.join(new_repo_path, ib_file)

                if not ib_path:
                    raise Error("infrabox file not found in %s" % new_repo_path)

                if ib_path in infrabox_paths:
                    raise Error("Recursive include detected")

                infrabox_paths[ib_path] = True
                c.collect("file: %s" % ib_path)
                yml = self.parse_infrabox_file(ib_path)

                git_repo = {
                    "clone_url": job['clone_url'],
                    "commit": job['commit'],
                    "infrabox_file": ib_file,
                    "full_history": True,
                    "branch": job.get('branch', None),
                    "github_api_token": self.repository.get('github_api_token', None)
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
                c.header("Parsing infrabox file", show=True)
                p = os.path.join(infrabox_context, job['infrabox_file'])
                c.collect("file: %s" % p)

                if p in infrabox_paths:
                    raise Error("Recursive include detected")

                infrabox_paths[p] = True

                yml = self.parse_infrabox_file(p)
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
                if not deps:
                    s['depends_on'] = job.get('depends_on', [])

                for d in deps:
                    job_with_children[d['job']] = True

                # overwrite env vars if set
                if 'environment' in job:
                    for n, v in job['environment'].items():
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
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_ROOT_URL')
    get_env('INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES')
    get_env('INFRABOX_LOCAL_CACHE_ENABLED')
    console = ApiConsole()

    j = None
    try:
        j = RunJob(console)
        j.main()
        j.console.header('Finished', show=True)

        with open('/dev/termination-log', 'w+') as out:
            out.write('Job finished successfully')

    except Failure as e:
        j.console.header('Failure', show=True)
        j.console.collect(e.message, show=True)

        with open('/dev/termination-log', 'w+') as out:
            out.write(e.message)

        sys.exit(ERR_EXIT_FAILURE)

    except Error as e:
        j.console.header('Error', show=True)
        j.console.collect(e.message, show=True)

        with open('/dev/termination-log', 'w+') as out:
            out.write(e.message)

        sys.exit(ERR_EXIT_ERROR)
    except:
        if j:
            j.console.header('An error occured', show=True)
            msg = traceback.format_exc()
            j.console.collect(msg, show=True)

            with open('/dev/termination-log', 'w+') as out:
                out.write(msg)

        sys.exit(ERR_EXIT_ERROR)

if __name__ == "__main__":
    main()
