#!/bin/sh -e
echo "## Link cache"
mkdir -p /infrabox/cache/node_modules
cp -r /infrabox/cache/node_modules /project/src/dashboard

cd /project/src/dashboard

echo "## npm install"
export NPM_CONFIG_LOGLEVEL=warn
npm install

echo "## Copy to cache"
rm -rf /infrabox/cache/node_modules
cp -r /project/src/dashboard/node_modules /infrabox/cache

set +e

echo "## Starting tests"
npm test -- -R xunit-file
rc=$?

set -e

cp xunit.xml /infrabox/upload/testresult

exit $rc
