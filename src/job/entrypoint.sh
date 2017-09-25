#!/bin/bash -e
mkdir -p /data/docker
mkdir -p /data/infrabox

if [ ! -e /var/run/docker.sock ]; then
    # Start docker daemon
    dockerd-entrypoint.sh --storage-driver overlay --graph /data/docker &

    # Wait until daemon is ready
    until docker version &> /dev/null; do
      sleep 1
    done
fi

mkdir -p ~/.ssh/

if [ -f /tmp/gerrit/id_rsa ]; then
    cp /tmp/gerrit/id_rsa ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -p $INFRABOX_GERRIT_PORT $INFRABOX_GERRIT_HOSTNAME >> ~/.ssh/known_hosts
fi

/job/job.py $@
