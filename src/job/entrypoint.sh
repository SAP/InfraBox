#!/bin/bash -e
mkdir -p /data/docker
mkdir -p /data/infrabox

if [ ! -e /var/run/docker.sock ]; then
    echo "Waiting for docker daemon to start up"
    # Start docker daemon
    dockerd-entrypoint.sh --storage-driver overlay --graph /data/docker &

    # Wait until daemon is ready
    until docker version &> /dev/null; do
      sleep 1
    done
else
    echo "Using host docker daemon socket"
fi

/job/job.py $@
