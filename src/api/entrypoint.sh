#!/bin/sh -e

echo "## Link cache"
mkdir -p /infrabox/cache/node_modules
cp -r /infrabox/cache/node_modules /project

cd project

echo "## npm install"
export NPM_CONFIG_LOGLEVEL=warn
npm install

echo "## Copy to cache"
rm -rf /infrabox/cache/node_modules
cp -r /project/node_modules /infrabox/cache

echo "## compiling server"
./node_modules/gulp/bin/gulp.js build-server

echo "## Copy to dist dir"
cp -r /project/dist  /api
cp -r /project/node_modules /api
cp /project/package.json /api

rm -rf /project/*

echo "## done"
