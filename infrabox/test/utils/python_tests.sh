#!/bin/sh

coverage run --source=.,$1 --branch test.py

rc=$?

set -e

coverage report -m
coverage xml

cp results.xml /infrabox/upload/testresult
cp coverage.xml /infrabox/upload/coverage

if [[ ! -z "$CODECOV_TOKEN" ]]; then
    if [[ -z "$INFRABOX_GIT_BRANCH" ]]; then
        codecov -t $CODECOV_TOKEN --root /infrabox/context -f coverage.xml
    else
        codecov -t $CODECOV_TOKEN --root /infrabox/context -f coverage.xml -b $INFRABOX_GIT_BRANCH
    fi
fi

exit $rc
