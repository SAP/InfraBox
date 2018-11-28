#!/bin/bash

coverage run --source=.,$1 --branch test.py

set -e

coverage report -m
coverage xml

if [ -e results.xml ]; then
    cp results.xml /infrabox/upload/testresult
fi

cp coverage.xml /infrabox/upload/coverage
