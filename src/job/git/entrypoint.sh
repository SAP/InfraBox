#!/bin/bash -e
mkdir -p ~/.ssh

if [ -f /tmp/gerrit/id_rsa ]; then
    echo "Setting private key"
    cp /tmp/gerrit/id_rsa ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -p $INFRABOX_GERRIT_PORT $INFRABOX_GERRIT_HOSTNAME >> ~/.ssh/known_hosts
else
    echo "No private key configured"
fi

python /git/api.py
