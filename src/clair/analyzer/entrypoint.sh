#!/bin/bash
set -e
DATABASE_URL="postgresql://$INFRABOX_DATABASE_USER:$INFRABOX_DATABASE_PASSWORD@localhost:5432/clair?sslmode=disable"
sed "s|DATABASE_URL|$DATABASE_URL|g" /config.yaml.template > /config.yaml
clair -config=/config.yaml
