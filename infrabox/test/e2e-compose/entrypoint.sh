#!/bin/sh -e
git clone https://github.com/InfraBox/cli.git /tmp/cli
cd /tmp/cli
pip install -e .

cd /infrabox/context/infrabox/test/e2e-compose/

set +e
python test.py
rc=$?

set -e

cp results.xml /infrabox/upload/testresult

exit $rc
