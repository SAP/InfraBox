#!/bin/sh -e
cp -r /infrabox/context/src/dashboard-client /dashboard

echo "## Link cache"
mkdir -p /infrabox/cache/node_modules
tar -C /infrabox/cache -cf - node_modules | tar -C /dashboard -xf -

cd /dashboard

echo "## npm install"

export NPM_CONFIG_LOGLEVEL=warn
npm install

echo "## build"
npm run build

echo "## Copy to cache"
rm -rf /infrabox/cache/node_modules
tar -C /dashboard -cf - node_modules | tar -C /infrabox/cache -xf -

echo "## Copy to output"
cp -r /dashboard/dist /infrabox/output

echo "## done"