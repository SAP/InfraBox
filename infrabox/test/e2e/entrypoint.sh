#!/bin/bash -ev

NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
IMAGE_TAG=build_135

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
    pip install infraboxcli

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
    export INFRABOX_CLI_TOKEN='d5c80d79-5355-4edb-bc18-7ba878e166bf'
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
          VALUES ('$INFRABOX_CLI_TOKEN', 'desc', '$PROJECT_ID', true, true)"
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
    mc mb minio/infrabox-container-output-bucket
    mc mb minio/infrabox-project-upload-bucket
    mc mb minio/infrabox-container-content-cache-bucket
    mc mb minio/infrabox-docker-registry-bucket
    mc ls minio
}

_deinstallInfrabox() {
    echo "## Deinstall infrabox"
    helm delete --tiller-namespace $NAMESPACE --purge infrabox || true
}

_installInfraboxMinio() {
    _deinstallInfrabox

    echo "## Install infrabox"
    outdir=/tmp/test
    rm -rf $outdir
    python /infrabox/context/deploy/install.py \
        -o $outdir \
        --platform kubernetes \
        --version $IMAGE_TAG \
        --general-worker-namespace $NAMESPACE \
        --general-system-namespace $NAMESPACE \
        --docker-registry quay.io/infrabox \
        --docker-registry-admin-username admin \
        --docker-registry-admin-password admin \
        --docker-registry-url http://infrabox-docker-registry.$NAMESPACE:8080 \
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
        --api-url http://infrabox-api.$NAMESPACE:8080 \
        --dashboard-url http://infrabox-dashboard.$NAMESPACE:8080 \
        --dashboard-secret secret \
        --docs-url http://infrabox-docs.$NAMESPACE:8080 \
        --job-api-url http://infrabox-job-api.$NAMESPACE:8080 \
        --job-api-secret kl23424

    pushd $outdir
    echo "{\"insecure-registries\": [\"infrabox-docker-registry.$NAMESPACE:8080\"]}" > config/docker/daemon.json
    ./install.sh
    popd

    _portForwardAPI
}

_runTests() {
    echo "## Run tests"
    pushd /infrabox/context/tests
    ./tests.sh
    popd
}

main() {
    _prepareKubectl
    _getDependencies
    _initHelm
    _installMinio
    _installPostgres
    _installInfraboxMinio
    _runTests
}

main
