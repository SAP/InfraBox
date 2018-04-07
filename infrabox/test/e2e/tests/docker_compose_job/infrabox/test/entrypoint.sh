#!/bin/sh
set -e

# Wait until the webserver is up and running
until $(curl --output /dev/null --silent --head --fail http://test-server:3000); do
    sleep 1
done

echo "## Run Tests"
cd /project/tests
nosetests -v .
