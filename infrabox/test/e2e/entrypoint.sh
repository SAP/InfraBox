#!/bin/bash -ev

NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
IMAGE_TAG=build_203

_prepareKubectl() {
    echo "## Prepare kubectl"
    kubectl config set-cluster default-cluster --server=${INFRABOX_RESOURCES_KUBERNETES_MASTER_URL} --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    kubectl config set-credentials default-admin --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt --token=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
    kubectl config set-context default-system --cluster=default-cluster --user=default-admin --namespace=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
    kubectl config use-context default-system

    kubectl get pods
}

_portForwardAPI() {
    # Port forward API
    api_pod=$(_getPodName "infrabox-api")

    echo "Port forwarding to API: '$api_pod'"
    kubectl port-forward -n $NAMESPACE $api_pod 8080 > /dev/null 2>&1 &
    until $(curl --output /dev/null --silent --head --fail http://localhost:8080/ping); do
      >&2 echo "API is unavailable - sleeping"
      sleep 1
    done
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

_sql() {
    psql -U postgres -d postgres -h localhost -c "$1" -A -t
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

    echo "## Prepare database"
    # Port forward postgres
    postgres_pod=$(_getPodName "postgres")
    echo "Port forwarding to postgres: '$postgres_pod'"
    kubectl port-forward -n $NAMESPACE $postgres_pod 5432 &

    # Wait until postgres is ready
    until psql -U postgres -h localhost -c '\l'; do
      >&2 echo "Postgres is unavailable - sleeping"
      sleep 1
    done

    echo "Postgres is ready"
    sleep 20 # wait until schema has been created

    echo "Inserting data"
    export TOKEN_ID='d5c80d79-5355-4edb-bc18-7ba878e166bf'
    export PROJECT_ID='2daef5b5-0474-4e63-a47e-df8438a82eba'
    export USER_ID='70c68f11-4d04-46d3-a68e-c0d2a91c00a6'
    # Insert dummy data
    _sql "INSERT INTO \"user\" (id, github_id, username, avatar_url)
          VALUES ('$USER_ID', '1', 'user', 'url')"
    _sql "INSERT INTO project (id, name, type)
          VALUES('$PROJECT_ID', 'test', 'upload')"

    _sql "INSERT INTO collaborator (project_id, user_id, owner)
          VALUES ('2daef5b5-0474-4e63-a47e-df8438a82eba', '70c68f11-4d04-46d3-a68e-c0d2a91c00a6', true)"
    _sql "INSERT INTO auth_token (id, description, project_id, scope_push, scope_pull)
          VALUES ('$TOKEN_ID', 'desc', '$PROJECT_ID', true, true)"
    _sql "INSERT INTO secret(project_id, name, value)
          VALUES ('$PROJECT_ID', 'SECRET_ENV', 'hello world')"
    echo "Finished preparing database"
}

_deinstallMinio() {
    echo "## Deinstall minio"
    helm delete --tiller-namespace $NAMESPACE --purge infrabox-minio || true
}

_installMinio() {
    _deinstallMinio

    echo "## Install minio"
    helm install --tiller-namespace $NAMESPACE stable/minio --set serviceType=ClusterIP,replicas=1,persistence.enabled=false -n infrabox-minio --namespace $NAMESPACE

    # Port forward API
    minio_pod=$(_getPodName "infrabox-minio")
    echo "Port forwarding to minio: '$minio_pod'"
    kubectl port-forward -n $NAMESPACE $minio_pod 9000 &

    sleep 30

    # init minio client
    mc config host add minio http://localhost:9000 AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY S3v4

    # Create buckets
    mc mb minio/infrabox-container-output
    mc mb minio/infrabox-project-upload
    mc mb minio/infrabox-container-cache
    mc mb minio/infrabox-docker-registry
    mc ls minio
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

    echo "## Install infrabox"
    outdir=/tmp/test
    rm -rf $outdir
    python /infrabox/context/deploy/install.py \
        -o $outdir \
        --platform kubernetes \
        --version $IMAGE_TAG \
        --general-dont-check-certificates \
        --root-url https://$ROOT_URL \
        --general-rbac-disabled \
        --general-worker-namespace $NAMESPACE \
        --general-system-namespace $NAMESPACE \
        --general-rsa-public-key ./id_rsa.pem \
        --general-rsa-private-key ./id_rsa \
        --docker-registry-admin-username admin \
        --docker-registry-admin-password admin \
        --database postgres \
        --postgres-host infrabox-postgres.$NAMESPACE \
        --postgres-username postgres \
        --postgres-password postgres \
        --postgres-database postgres \
        --storage s3 \
        --s3-endpoint infrabox-minio-minio-svc.$NAMESPACE \
        --s3-secure false \
        --s3-secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
        --s3-access-key AKIAIOSFODNN7EXAMPLE \
        --s3-region us-east-1 \
        --s3-port 9000 \

    pushd $outdir/infrabox
    helm install --tiller-namespace $NAMESPACE --namespace $NAMESPACE .
    popd

    export INFRABOX_CLI_TOKEN=$(python /infrabox/context/infrabox/test/e2e/create_token.py ./id_rsa $PROJECT_ID $TOKEN_ID)
    export INFRABOX_API_URL=http://localhost:8080/api

    _portForwardAPI
}

_runTests() {
    echo "## Run tests"
    pushd /infrabox/context/infrabox/test/e2e/tests
    ./tests.sh
    popd
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
