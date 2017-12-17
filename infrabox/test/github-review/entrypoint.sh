#!/bin/sh -e

cd tests
coverage run --source=. --branch tests.py
coverage xml

cp coverage.xml /infrabox/upload/coverage
cp results.xml /infrabox/upload/testresult
