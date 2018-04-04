#!/bin/sh
set -e

echo "## Link cache"
mkdir -p /infrabox/cache/node_modules
cp -r /infrabox/cache/node_modules /project

cd project

echo "## npm install"
export NPM_CONFIG_LOGLEVEL=warn
npm install

echo "## Copy to cache"
rm -rf /infrabox/cache/node_modules
mkdir -p /infrabox/cache/node_modules
cp -Lr /project/node_modules/* /infrabox/cache/node_modules


echo "## Start server"
node index.js
