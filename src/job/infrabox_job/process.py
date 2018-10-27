import subprocess
import sys

class Failure(Exception):
    def __init__(self, message):
        super(Failure, self).__init__(message)
        self.message = message

class ApiConsole(object):
    def __init__(self):
        pass

    def collect(self, line, show=False):
        if show:
            print line
            sys.stdout.flush()

    def execute(self, command, cwd=None, shell=False, show=False, env=None, ignore_error=False, show_cmd=True):
        if show_cmd:
            self.collect(' '.join(command) + '\n', show=show)

        p = subprocess.Popen(command, cwd=cwd, env=env, shell=shell)
        p.wait()

        if p.returncode != 0 and not ignore_error:
            raise Exception('Command failed')

    def header(self, h, show=False):
        h = "## " + h + '\n'
        self.collect(h, show=show)
        self.collect(('=' * len(h)) + "\n", show=False)
