#!/bin/sh -e

HTPASSWD_PATH=/home/nginx/nginx.htpasswd python get_admin_pw.py

sed -i -e "s/auth-host-placeholder/$INFRABOX_AUTH_HOST/g" /etc/nginx/nginx.conf
sed -i -e "s/registry-host-placeholder/$INFRABOX_REGISTRY_HOST/g" /etc/nginx/nginx.conf

nginx -g "daemon off;"
