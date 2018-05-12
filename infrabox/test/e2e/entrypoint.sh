#!/bin/bash -ev

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

    kubectl create ns infrabox-worker
    kubectl create ns infrabox-system
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
    kubectl get pods -n $1 | grep $2 | grep Running | awk '{print $1}'
}

_getNginxIP() {
    kubectl get services --all-namespaces

    external_ip=""
    while [ -z $external_ip ]; do
        echo "Waiting for nginx endpoint..."
        external_ip=$(kubectl -n kube-system get svc nic-nginx-ingress-controller --template="{{range .status.loadBalancer.ingress}}{{.ip}}{{end}}")
        [ -z "$external_ip" ] && sleep 10
    done

    echo "Nginx endpoint: $external_ip"
    echo $external_ip
}

_getPodName() {
    pod_name=$(_getPodNameImpl $1 $2)

    while true; do
        if [ -n "$pod_name" ]; then
           break
        fi

        sleep 1
        pod_name=$(_getPodNameImpl $1 $2)
    done
    echo $pod_name
}

_initHelm() {
    echo "## init helm"
    kubectl -n kube-system create sa tiller
    kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
    helm init --service-account tiller

    echo "## Wait for tiller to be ready"
    # wait for tiller to be ready
    tiller_pod=$(_getPodName "kube-system" "tiller")
    sleep 20
}

_installPostgres() {
    echo "## Install postgres"
    kubectl run postgres --image=quay.io/infrabox/postgres:$IMAGE_TAG -n infrabox-system
    kubectl expose -n infrabox-system deployment postgres --port 5432 --target-port 5432 --name infrabox-postgres

    # Wait until postgres is ready
    postgres_pod=$(_getPodName "infrabox-system" "postgres")
    echo "Port forwarding to postgres: '$postgres_pod'"
    kubectl port-forward -n infrabox-system $postgres_pod 5432 &

    # Wait until postgres is ready
    until psql -U postgres -h localhost -c '\l'; do
        >&2 echo "Postgres is unavailable - sleeping"
        sleep 1
    done
}

_installMinio() {
    echo "## Install minio"
    helm install \
        --set serviceType=ClusterIP,replicas=1,persistence.enabled=false \
        -n infrabox-minio \
        --namespace infrabox-system \
        stable/minio

    # Wait until minio is ready
    sleep 30

    # init minio client
    minio_pod=$(_getPodName "infrabox-system" "minio")
    echo "Port forwarding to minio: '$minio_pod'"
    kubectl get pod --all-namespaces
    kubectl port-forward -n infrabox-system $minio_pod 9000 &

    until mc config host add minio http://localhost:9000 AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY S3v4;
    do
        echo "Waiting for minio to be ready"
        sleep 3
    done

    # Create buckets
    mc mb minio/infrabox
}

_installNginxIngress() {
    echo "## Install nginx ingress"

    helm install \
        -n nic \
        --namespace kube-system
        --set controller.config.proxy-body-size="0" \
        --set controller.config.ssl-redirect='"false"' \
        stable/nginx-ingress

    nginx_ip=$(_getNginxIP)

    export ROOT_URL="$nginx_ip.nip.io"
    echo "Generating certs for: $ROOT_URL"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /tmp/tls.key -out /tmp/tls.crt -subj "/CN=$ROOT_URL"

    kubectl create -n infrabox-system secret tls infrabox-tls-certs --key /tmp/tls.key --cert /tmp/tls.crt
}

_installInfrabox() {
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
        --general-rsa-public-key ./id_rsa.pem \
        --general-rsa-private-key ./id_rsa \
        --admin-email admin@infrabox.net \
        --admin-password admin \
        --database postgres \
        --postgres-host infrabox-postgres.infrabox-system \
        --postgres-username postgres \
        --postgres-password postgres \
        --postgres-database postgres \
        --storage s3 \
        --s3-endpoint infrabox-minio.infrabox-system \
        --s3-bucket infrabox \
        --s3-secure false \
        --s3-secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
        --s3-access-key AKIAIOSFODNN7EXAMPLE \
        --s3-region us-east-1 \
        --s3-port 9000

    pushd $outdir/infrabox
    helm install --namespace infrabox-system .
    popd

    export INFRABOX_DATABASE_HOST=infrabox-postgres.infrabox-system
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
    _installPostgres
    _installMinio
    _installNginxIngress
    _installInfrabox
    _runTests
}

main
