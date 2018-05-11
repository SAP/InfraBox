#!/bin/bash -ev

NAMESPACE=infrabox-system
IMAGE_TAG=build_$INFRABOX_BUILD_NUMBER

_prepareKubectl() {
    echo "## Prepare kubectl"

	SERVICE_NAME="e2e-cluster"

	CA_CRT="/var/run/infrabox.net/services/$SERVICE_NAME/ca.crt"
	CLIENT_CRT="/var/run/infrabox.net/services/$SERVICE_NAME/client.crt"
	CLIENT_KEY="/var/run/infrabox.net/services/$SERVICE_NAME/client.key"


	ENDPOINT=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/endpoint)
	PASSWORD=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/password)
	USERNAME=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/username)

	kubectl config set-cluster $SERVICE_NAME \
		--server=$ENDPOINT \
		--certificate-authority=$CA_CRT

	kubectl config set-credentials admin \
		--certificate-authority=$CA_CRT \
		--client-certificate=$CLIENT_CRT \
		--client-key=$CLIENT_KEY \
		--username=$USERNAME \
		--password=$PASSWORD

	kubectl config set-context default-system \
		--cluster=$SERVICE_NAME \
		--user=admin

    kubectl config use-context default-system

    kubectl get nodes
}

_getDependencies() {
    echo "## install infraboxcli"
    # pip install infraboxcli
    git clone https://github.com/InfraBox/cli.git /cli
    pushd /cli
    pip install -e .
    popd

    echo "## Get minio client"
    curl https://dl.minio.io/client/mc/release/linux-amd64/mc > /usr/bin/mc
    chmod +x /usr/bin/mc
}

_getPodNameImpl() {
    kubectl get pods -n $NAMESPACE | grep $1 | grep Running | awk '{print $1}'
}

_getPodName() {
    pod_name=$(_getPodNameImpl $1)

    while true; do
        if [ -n "$pod_name" ]; then
           break
        fi

        sleep 1
        pod_name=$(_getPodNameImpl $1)
    done
    echo $pod_name
}

_initHelm() {
    echo "## init helm"
    helm init --tiller-namespace $NAMESPACE

    echo "## Wait for tiller to be ready"
    # wait for tiller to be ready
    tiller_pod=$(_getPodName "tiller")
    sleep 20
}

_deinstallPostgres() {
    echo "## Deinstall postgres"
    helm delete --tiller-namespace $NAMESPACE --purge infrabox-postgres || true
}

_installPostgres() {
    _deinstallPostgres

    echo "## Install postgres"
    kubectl run postgres --image=quay.io/infrabox/postgres:$IMAGE_TAG -n $NAMESPACE
    kubectl expose -n $NAMESPACE deployment postgres --port 5432 --target-port 5432 --name infrabox-postgres

    # Wait until postgres is ready
    until psql -U postgres -h infrabox-postgres.$NAMESPACE -c '\l'; do
        >&2 echo "Postgres is unavailable - sleeping"
        sleep 1
    done
}

_deinstallMinio() {
    echo "## Deinstall minio"
    helm delete --tiller-namespace $NAMESPACE --purge infrabox-minio || true
}

_installMinio() {
    _deinstallMinio

    echo "## Install minio"
    helm install --tiller-namespace $NAMESPACE \
        --set serviceType=ClusterIP,replicas=1,persistence.enabled=false \
        -n infrabox-minio \
        --namespace $NAMESPACE \
        stable/minio

    sleep 30

    # init minio client
    mc config host add minio \
        http://infrabox-minio.$NAMESPACE:9000 \
        AKIAIOSFODNN7EXAMPLE \
        wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
        S3v4

    # Create buckets
    mc mb minio/infrabox
}

_installNginxIngress() {
    echo "## Install nginx ingress"

    export ROOT_URL="nic-nginx-ingress-c.$NAMESPACE"
    echo "Generating certs for: $ROOT_URL"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /tmp/tls.key -out /tmp/tls.crt -subj "/CN=$ROOT_URL"

    kubectl create -n $NAMESPACE secret tls infrabox-tls-certs --key /tmp/tls.key --cert /tmp/tls.crt

    helm install \
        --tiller-namespace $NAMESPACE \
        -n nic \
        --namespace $NAMESPACE \
        --set controller.scope.enabled="true" \
        --set controller.scope.namespace="$NAMESPACE" \
        --set controller.service.type="ClusterIP" \
        --set controller.name="c" \
        --set controller.config.proxy-body-size="0" \
        --set controller.config.ssl-redirect='"false"' \
        stable/nginx-ingress
}

_deinstallInfrabox() {
    echo "## Deinstall infrabox"
    helm delete --tiller-namespace $NAMESPACE --purge infrabox || true
}

_installInfrabox() {
    _deinstallInfrabox

    ssh-keygen -N '' -t rsa -f id_rsa
    ssh-keygen -f id_rsa.pub -e -m pem > id_rsa.pem

    mkdir -p /var/run/secrets/infrabox.net/rsa/
    cp id_rsa* /var/run/secrets/infrabox.net/rsa/

    echo "## Install infrabox"
    outdir=/tmp/test
    rm -rf $outdir
    python /infrabox/context/deploy/install.py \
        -o $outdir \
        --general-dont-check-certificates \
        --version $IMAGE_TAG \
        --root-url https://$ROOT_URL \
        --general-rbac-disabled \
        --general-worker-namespace $NAMESPACE \
        --general-system-namespace $NAMESPACE \
        --general-rsa-public-key ./id_rsa.pem \
        --general-rsa-private-key ./id_rsa \
        --admin-email admin@infrabox.net \
        --admin-password admin \
        --database postgres \
        --postgres-host infrabox-postgres.$NAMESPACE \
        --postgres-username postgres \
        --postgres-password postgres \
        --postgres-database postgres \
        --storage s3 \
        --s3-endpoint infrabox-minio.$NAMESPACE \
        --s3-bucket infrabox \
        --s3-secure false \
        --s3-secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
        --s3-access-key AKIAIOSFODNN7EXAMPLE \
        --s3-region us-east-1 \
        --s3-port 9000

    pushd $outdir/infrabox
    helm install --tiller-namespace $NAMESPACE --namespace $NAMESPACE .
    popd

    export INFRABOX_DATABASE_HOST=infrabox-postgres.$NAMESPACE
    export INFRABOX_DATABASE_DB=postgres
    export INFRABOX_DATABASE_USER=postgres
    export INFRABOX_DATABASE_PORT=5432
    export INFRABOX_DATABASE_PASSWORD=postgres
    export INFRABOX_URL=https://$ROOT_URL
    export INFRABOX_ROOT_URL=https://$ROOT_URL
}

_runTests() {
    echo "## Run tests"
    pushd /infrabox/context/infrabox/test/e2e

    set +e
    python test.py
    rc=$?

    cp results.xml /infrabox/upload/testresult

    exit $rc
}

main() {
    _prepareKubectl
    _getDependencies
    _initHelm
    _installMinio
    _installPostgres
    _installNginxIngress
    _installInfrabox
    _runTests
}

main
