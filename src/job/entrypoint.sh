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

/job/job.py $@
