#!/bin/sh

cd tests
coverage run --source=. --branch tests.py
rc=$?

set -e

coverage xml

echo "## Get infrabox testresult"
git clone https://github.com/InfraBox/testresult.git /tmp/infrabox-testresult

echo "## Download coverage"
git clone https://github.com/InfraBox/coverage.git /tmp/infrabox-coverage

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
