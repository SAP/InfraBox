#!/bin/sh -e
cd /test

echo "Running nosetests"
nosetests .

echo "Finished running tests"
