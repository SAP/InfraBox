#!/bin/sh -e

cd tests
coverage run --source=. --branch tests.py
coverage xml

cp results.xml /infrabox/upload/testresult
cp coverage.xml /infrabox/upload/coverage
