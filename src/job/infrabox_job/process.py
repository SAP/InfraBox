import subprocess
import sys
import time
import random

class Failure(Exception):
    def __init__(self, message):
        super(Failure, self).__init__(message)
        self.message = message

class ApiConsole(object):
    def __init__(self):
        pass

    def collect(self, line, show=False):
        if show:
            try:
                print line
            except UnicodeEncodeError:
                print line.encode('utf-8')
            sys.stdout.flush()

    def execute(self, command, cwd=None, shell=False, show=False, env=None, ignore_error=False, show_cmd=True, retry=False):
        for _ in range(0, 5):
            if show_cmd:
                self.collect(' '.join(command), show=show)

            p = subprocess.Popen(command, cwd=cwd, env=env, shell=shell)
            p.wait()

            if p.returncode == 0:
                return

            if not retry:
                break

            t = random.randint(10, 100)
            self.collect('Command failed, retrying in %s seconds' % t, show=show)
            time.sleep(t)

        if p.returncode != 0 and not ignore_error:
            raise Exception('Command failed')

    def header(self, h, show=False):
        h = "## " + h
        self.collect(h, show=show)
        self.collect(('=' * len(h)), show=False)

    def print_failure(self, message):
        message = "### [level=error] " + message
        self.collect(message, show=True)
