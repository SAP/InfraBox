#!/bin/bash -e
mkdir -p /data/docker
mkdir -p /data/infrabox
mkdir -p ~/.ssh

if [ ! -e /var/run/docker.sock ]; then
    echo "Waiting for docker daemon to start up"
    # Start docker daemon
    dockerd-entrypoint.sh --storage-driver overlay --data-root /data/docker &

    # Wait until daemon is ready
    COUNTER=0
    until docker version &> /dev/null; do
      let COUNTER=COUNTER+1
      sleep 1

      if [ $COUNTER -gt 60 ]; then
        echo "Docker daemon not started" > '/dev/termination-log'
        exit 1
      fi
    done
else
    echo "Using host docker daemon socket"
fi

if [ -f /tmp/gerrit/id_rsa ]; then
    echo "Setting private key"
    eval `ssh-agent -s`
    cp /tmp/gerrit/id_rsa ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    echo "StrictHostKeyChecking no" > ~/.ssh/config
    ssh-add ~/.ssh/id_rsa
    ssh-keyscan -p $INFRABOX_GERRIT_PORT $INFRABOX_GERRIT_HOSTNAME >> ~/.ssh/known_hosts
else
    echo "No private key configured"
fi

/job/job.py $@
