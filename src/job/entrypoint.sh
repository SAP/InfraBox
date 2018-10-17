#!/bin/bash -e
mkdir -p /data/docker
mkdir -p /data/infrabox
mkdir -p /data/tmp
mkdir -p /data/repo
mkdir -p ~/.ssh

if [ ! -e /var/run/docker.sock ]; then
    echo "Docker Daemon Config"
    cat /etc/docker/daemon.json
    echo ""

    echo "Waiting for docker daemon to start up"

    # Start docker daemon
    nohup dockerd-entrypoint.sh --storage-driver $INFRABOX_JOB_STORAGE_DRIVER --data-root /data/docker > /tmp/dockerd.log &

    # Wait until daemon is ready
    COUNTER=0
    until docker version &> /dev/null; do
      let COUNTER=COUNTER+1
      sleep 1

      if [ $COUNTER -gt 60 ]; then
        echo "Docker daemon not started" > '/dev/termination-log'
        cat /tmp/dockerd.log >> /dev/termination-log
        exit 1
      fi
    done
else
    echo "Using host docker daemon socket"
fi

if [ ! -z "$INFRABOX_GIT_PRIVATE_KEY" ]; then
    echo "Setting private key"
    eval `ssh-agent -s`
    echo $INFRABOX_GIT_PRIVATE_KEY > ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    echo "StrictHostKeyChecking no" > ~/.ssh/config
    ssh-add ~/.ssh/id_rsa
    ssh-keyscan -p $INFRABOX_GIT_PORT $INFRABOX_GIT_HOSTNAME >> ~/.ssh/known_hosts
else
    echo "No private key configured"
fi

/job/job.py $@
