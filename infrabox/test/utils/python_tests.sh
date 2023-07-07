#!/bin/bash
set -ex

coverage run --source=.,$1 --branch test.py

coverage report -m
coverage xml

if [ -e results.xml ]; then
    cp results.xml /infrabox/upload/testresult
fi

cp coverage.xml /infrabox/upload/coverage
