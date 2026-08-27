#!/bin/bash -e
mkdir -p /data/docker
mkdir -p /data/infrabox
mkdir -p /data/tmp
mkdir -p /data/repo
mkdir -p ~/.ssh
mkdir -p /root/.docker

if [ -f /tmp/docker-secret/config.json ]; then
    cp /tmp/docker-secret/config.json /root/.docker/config.json
    echo "Docker config copied from secret"
fi


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

    # DM01-5956: Install SAP Root CA for InfraBox internal registries so that
    # Docker's built-in BuildKit (docker driver, DOCKER_BUILDKIT=1) can import
    # cache manifests via --cache-from without x509 errors.
    # Note: /etc/buildkit/buildkitd.toml is only read by a standalone buildkitd
    # process, NOT by the Docker daemon's built-in BuildKit driver.
    if [ -f /etc/ssl/certs/saprootca.pem ]; then
        echo "Installing SAP Root CA into /etc/docker/certs.d/ for InfraBox registries"
        for registry in \
            "test-new.infrabox.datahub.only.sap" \
            "infrabox.datahub.only.sap" \
            "ha-eu-de-1.infrabox.datahub.only.sap" \
            "ha-eu-de-1b.infrabox.datahub.only.sap" \
            "ha-eu-de-2.infrabox.datahub.only.sap" \
            "ha-eu-de-2b.infrabox.datahub.only.sap" \
            "gardener-eu-de-1.infrabox.datahub.only.sap" \
            "gardener-eu-de-2.infrabox.datahub.only.sap"; do
            mkdir -p "/etc/docker/certs.d/${registry}"
            cp /etc/ssl/certs/saprootca.pem "/etc/docker/certs.d/${registry}/ca.crt"
        done
        echo "SAP Root CA installed for $(ls /etc/docker/certs.d/ | wc -l) registries"

        # DM01-6122: The previous fix (appending to ca-certificates.crt) did not work because
        # Docker 23's embedded BuildKit reads the system CA bundle that was compiled into the
        # dockerd binary, not the file on disk at runtime. The correct approach is to drop the
        # CA into /usr/local/share/ca-certificates/ and run update-ca-certificates, which
        # rebuilds ca-certificates.crt before dockerd starts and is the mechanism the Alpine
        # ca-certificates package officially supports for adding custom CAs.
        cp /etc/ssl/certs/saprootca.pem /usr/local/share/ca-certificates/saprootca.crt
        update-ca-certificates
        echo "SAP Root CA registered via update-ca-certificates for BuildKit"
    fi

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
