#!/bin/bash -e
mkdir -p ~/.ssh/

cp /tmp/gerrit/id_rsa ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa
ssh-keyscan -p $INFRABOX_GERRIT_PORT $INFRABOX_GERRIT_HOSTNAME >> ~/.ssh/known_hosts

python /trigger.py
