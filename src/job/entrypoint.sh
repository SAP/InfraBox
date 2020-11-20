#!/bin/bash -e
mkdir -p /data/docker
mkdir -p /data/infrabox
mkdir -p /data/tmp
mkdir -p /data/repo
mkdir -p ~/.ssh


function startDocker() {
    # Start docker daemon
    nohup dockerd-entrypoint.sh --storage-driver $INFRABOX_JOB_STORAGE_DRIVER --data-root /data/docker &> /tmp/dockerd.log &
    sleep 5
    # Wait until daemon is ready
    COUNTER=0
    until docker version &> /dev/null; do
      let COUNTER=COUNTER+1
      sleep 1

      if [ $COUNTER -gt 60 ]; then
        return 1
      fi
    done
    return 0
}


if [ ! -e /var/run/docker.sock ]; then
    echo "Docker Daemon Config"
    cat /etc/docker/daemon.json
    echo ""

    echo "Waiting for docker daemon to start up"
    CNT=0
    while true; do
        if [ $CNT -gt 3 ]; then
            echo "Docker daemon not started" | tee '/dev/termination-log'
            cat /tmp/dockerd.log | tee -a /dev/termination-log
            exit 1
        fi
        let CNT=CNT+1

        if startDocker ; then
            echo "Docker daemon started."
            break
        else
            echo "Docker daemon not started, retry"
            sleep 60
        fi
    done
else
    echo "Using host docker daemon socket"
fi

if [ ! -z "$INFRABOX_GIT_PRIVATE_KEY" ]; then
    echo "Setting private key"
    eval `ssh-agent -s`
    echo "$INFRABOX_GIT_PRIVATE_KEY" > ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    echo "StrictHostKeyChecking no" > ~/.ssh/config
    ssh-add ~/.ssh/id_rsa
    ssh-keyscan -p $INFRABOX_GIT_PORT $INFRABOX_GIT_HOSTNAME >> ~/.ssh/known_hosts || true
else
    echo "No private key configured"
fi

echo "CLUSTER: $INFRABOX_CLUSTER_NAME"
echo "DOCKER VERSION: $(docker -v)"
echo "DOCKER_COMPOSE VERSION: $(docker-compose -v)"

exec /job/job.py $@
