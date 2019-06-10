#!/bin/bash -e
export INFRABOX_VERSION=local
export INFRABOX_DATABASE_DB=infrabox
export INFRABOX_DATABASE_USER=infrabox
export INFRABOX_DATABASE_PASSWORD=9unfcs87gh3ASd8asd
export INFRABOX_DATABASE_HOST=localhost
export INFRABOX_DATABASE_PORT=5433
export PYTHONPATH=..

python -u JSONserver.py
