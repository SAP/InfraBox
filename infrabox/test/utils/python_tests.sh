#!/bin/sh

cd tests
coverage run --source=.,/auth --branch test.py
rc=$?

set -e

coverage report -m
coverage xml

echo "## Create coverage result"
export PYTHONPATH=/
python /tmp/infrabox-coverage/coverage.py \
    --output /infrabox/upload/markup/coverage.json \
    --input coverage.xml \
    --badge /infrabox/upload/badge/coverage.json \
    --format py-coverage

echo "## Convert test result"
python /tmp/infrabox-testresult/testresult.py -f xunit -i results.xml

exit $rc
