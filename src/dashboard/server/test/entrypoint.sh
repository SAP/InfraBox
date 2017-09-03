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
cp -r /project/src/dashboard/node_modules /infrabox/cache/

echo "## compiling server"
./node_modules/.bin/gulp build-server

echo "## starting server"
node ./dist/server/app.js
