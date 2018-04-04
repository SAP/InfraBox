#!/bin/sh

cd tests
coverage run --source=. --branch tests.py
rc=$?

set -e
coverage xml

ls -al /infrabox/upload/
cp coverage.xml /infrabox/upload/coverage
cp results.xml /infrabox/upload/testresult

exit $rc
