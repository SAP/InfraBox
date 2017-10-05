import subprocess
import os

def execute(args, cwd=None):
    subprocess.check_call(args, cwd=cwd)

def main():
    commit = os.environ['INFRABOX_COMMIT']
    clone_url = os.environ['INFRABOX_CLONE_URL']
    branch = os.environ.get('INFRABOX_BRANCH', None)
    ref = os.environ.get('INFRABOX_REF', None)

    cmd = ['git', 'clone', '--depth=10']
    if branch:
        cmd += ['--single-branch', '-b', branch]

    print "## Clone repository"
    cmd += [clone_url, '/repo']

    print ' '.join(cmd)
    execute(cmd)

    if ref:
        cmd = ['git', 'fetch', '--depth=10', clone_url, ref]
        print ' '.join(cmd)
        execute(cmd, cwd="/repo")

    print "#Checkout commit"
    cmd = ['git', 'checkout', '-qf', '-b', 'job', commit]

    print ' '.join(cmd)
    execute(cmd, cwd="/repo")

    print "## Init submodules"
    execute(['git', 'submodule', 'init'], cwd="/repo")
    execute(['git', 'submodule', 'update'], cwd="/repo")

if __name__ == "__main__":
    main()
