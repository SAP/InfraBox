#!/bin/bash -e

if [ "$INFRABOX_DOCS_TLS_ENABLED" == "true" ];
then
    if [ ! -f "/var/run/infrabox/server.crt" ]; then
        echo "/var/run/infrabox/server.crt not found"
        exit 1
    fi

    if [ ! -f "/var/run/infrabox/server.key" ]; then
        echo "/var/run/infrabox/server.key not found"
        exit 1
    fi

    cp /etc/nginx/nginx_ssl.conf /etc/nginx/nginx.conf
else
    cp /etc/nginx/nginx_no_ssl.conf /etc/nginx/nginx.conf
fi

nginx -g "daemon off;"
