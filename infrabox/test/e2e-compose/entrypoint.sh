#!/bin/sh -e
git clone https://github.com/InfraBox/cli.git /tmp/cli
cd /tmp/cli
pip install -e .

cd /infrabox/context/infrabox/test/e2e-compose/

set +e
coverage run --source=.,$1 --branch test.py
rc=$?

set +e

coverage report -m
coverage xml

cp results.xml /infrabox/upload/testresult
cp coverage.xml /infrabox/upload/coverage

exit $rc
