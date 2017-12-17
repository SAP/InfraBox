#!/bin/sh -e

cd tests
coverage run --source=. --branch tests.py
coverage xml

ls -al /infrabox/upload/
cp coverage.xml /infrabox/upload/coverage
cp results.xml /infrabox/upload/testresult
