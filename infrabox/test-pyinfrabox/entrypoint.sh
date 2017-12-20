#!/bin/sh -e
echo "## Run tests"
nosetests \
    --with-xunit \
    --with-coverage \
    --cover-xml \
    --cover-branches \
    --cover-package=pyinfrabox \
    --cover-tests tests/*

cp coverage.xml /infrabox/upload/coverage
cp nosetests.xml /infrabox/upload/testresult
