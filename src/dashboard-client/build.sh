#!/bin/sh -e
cp -r /infrabox/context/src/dashboard-client /dashboard

echo "## Link cache"
if [ -d /infrabox/cache/node_modules ]; then
    mv /infrabox/cache/node_modules /dashboard/node_modules
else
    mkdir -p /dashboard/node_modules
fi

cd /dashboard

echo "## npm install"

export NPM_CONFIG_LOGLEVEL=warn
npm install

echo "## build"
npm run build

echo "## Copy to output"
cp -r /dashboard/dist /infrabox/output

echo "## done"