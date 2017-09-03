#!/bin/sh -e
cd /project/infrabox/test/create-jobs

echo "Running nosetests"
nosetests .

echo "Finished running tests"
