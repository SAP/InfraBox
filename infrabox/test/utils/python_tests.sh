#!/bin/sh -e

cd /tests
coverage run --source=.,$1 --branch test.py

coverage report -m
coverage xml

cp results.xml /infrabox/upload/testresult
cp coverage.xml /infrabox/upload/coverage
