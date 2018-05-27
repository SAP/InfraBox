#!/bin/bash -e
mkdir -p /data/docker
mkdir -p /data/infrabox

if [ ! -e /var/run/docker.sock ]; then
    mkdir -p /etc/docker
    echo $INFRABOX_JOB_DAEMON_JSON > /etc/docker/daemon.json

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

/job/job.py $@
