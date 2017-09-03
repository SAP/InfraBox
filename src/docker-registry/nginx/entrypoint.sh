#!/bin/sh
set -e

HTPASSWD_PATH=/home/nginx/nginx.htpasswd python get_admin_pw.py
nginx -g "daemon off;"
