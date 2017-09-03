#!/bin/sh -e
echo "## Get infrabox testresult"
git clone https://github.com/InfraBox/testresult.git /tmp/infrabox-testresult

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

echo "## Starting tests"
npm test -- -R xunit-file

echo "## Converting testresult"
python /tmp/infrabox-testresult/testresult.py -f xunit -i xunit.xml
