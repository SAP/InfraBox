#!/bin/bash -e

# Settings
cluster_name="t-$INFRABOX_JOB_ID"
cluster_zone="us-east1-c"
cluster_project="test-kubernetes-167921"
cluster_version="1.6.4"
cluster_docker_registry="us.gcr.io/test-kubernetes-167921"
test_base_path="/project/infrabox/test-kubernetes/tests"

# Functions
_sql() {
    psql -U postgres -d test_db -h localhost -c "$1" -A -t
}

_getPodNameImpl() {
    kubectl get pods --all-namespaces | grep $1 | grep Running | awk '{print $2}'
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

_deinstallPostgres() {
    echo "## Deinstall postgres"
    helm delete --purge infrabox-postgres || true
}

_installPostgres() {
    _deinstallPostgres

    echo "## Install postgres"
    pushd /project/helm/infrabox-postgres
    helm install -n infrabox-postgres \
        --set docker_registry=$cluster_docker_registry \
        --set tag="build_$INFRABOX_BUILD_NUMBER" .
    popd

    echo "## Prepare database"
    # Port forward postgres
    postgres_pod=$(_getPodName "postgres")
    kubectl get pods --all-namespaces
    echo "Port forwarding to postgres: '$postgres_pod'"
    kubectl port-forward -n infrabox-system $postgres_pod 5432 &

    sleep 20 # wait until schema has been created

    # Wait until postgres is ready
    until psql -U postgres -h localhost -c '\l'; do
      >&2 echo "Postgres is unavailable - sleeping"
      sleep 1
    done

    export INFRABOX_CLI_TOKEN='d5c80d79-5355-4edb-bc18-7ba878e166bf'
    export INFRABOX_CLI_PROJECT_ID='2daef5b5-0474-4e63-a47e-df8438a82eba'
    export USER_ID='70c68f11-4d04-46d3-a68e-c0d2a91c00a6'
    # Insert dummy data
    _sql "INSERT INTO \"user\" (id, github_id, username, avatar_url)
          VALUES ('$USER_ID', '1', 'user', 'url')"
    _sql "INSERT INTO project (id, name, type)
          VALUES('$INFRABOX_CLI_PROJECT_ID', 'test', 'upload')"

    _sql "INSERT INTO collaborator (project_id, user_id, owner)
          VALUES ('2daef5b5-0474-4e63-a47e-df8438a82eba', '70c68f11-4d04-46d3-a68e-c0d2a91c00a6', true)"
    _sql "INSERT INTO auth_token (token, description, user_id, scope_push, scope_pull)
          VALUES ('$INFRABOX_CLI_TOKEN', 'desc', '70c68f11-4d04-46d3-a68e-c0d2a91c00a6', true, true)"
    _sql "INSERT INTO secret(project_id, name, value)
          VALUES ('$INFRABOX_CLI_PROJECT_ID', 'SECRET_ENV', 'hello world')"
    _sql "INSERT INTO user_quota(user_id, max_concurrent_jobs, max_cpu_per_job, max_memory_per_job, max_jobs_per_build)
          VALUES ('$USER_ID', 2, 2, 4096, 20)"
}

_createKubernetesObjects() {
    # Create namespaces
    kubectl create namespace infrabox-system
    kubectl create namespace infrabox-worker

    # create credentials
    kubectl -n infrabox-system create secret generic infrabox-gcs --from-file=/test/gcs_service_account.json
    kubectl -n infrabox-worker create secret generic infrabox-gcs --from-file=/test/gcs_service_account.json

    kubectl -n infrabox-system create secret generic infrabox-dashboard \
            --from-literal=secret=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

    kubectl -n infrabox-system create secret generic infrabox-docker-registry \
            --from-literal=username=admin \
            --from-literal=password=admin

    kubectl -n infrabox-worker create secret generic infrabox-docker-registry \
            --from-literal=username=admin \
            --from-literal=password=admin

    kubectl -n infrabox-system create secret generic infrabox-s3-credentials \
            --from-literal=accessKey=AKIAIOSFODNN7EXAMPLE \
            --from-literal=secretKey=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

    kubectl -n infrabox-worker create secret generic infrabox-s3-credentials \
            --from-literal=accessKey=AKIAIOSFODNN7EXAMPLE \
            --from-literal=secretKey=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
}

_createKubernetesCluster() {
    echo "## Create cluster"
    gcloud container clusters create $cluster_name \
        --zone $cluster_zone \
        --cluster-version $cluster_version \
        --disk-size=50 \
        --image-type=COS \
        --machine-type=custom-1-3072 \
        --node-labels=infrabox-machine-type=vm-1-2048 \
        --preemptible \
        --enable-autoscaling \
        --num-nodes=3 \
        --min-nodes=3 \
        --max-nodes=5 \
        --no-enable-legacy-authorization
}

_createCluster() {
    echo "## Activate account"
    mkdir /test
    echo $TEST_KUBERNETES_SERVICE_ACCOUNT > /test/gcs_service_account.json

    gcloud auth activate-service-account --key-file /test/gcs_service_account.json
    gcloud config set project $cluster_project
    gcloud config set compute/zone $cluster_zone

    _createKubernetesCluster
    trap 'gcloud container clusters delete --quiet --async $cluster_name' EXIT

    gcloud config set container/cluster $cluster_name
    gcloud container clusters get-credentials $cluster_name

    # install helm
    helm init

    _createKubernetesObjects

    # wait for tiller to be ready
    tiller_pod=$(_getPodName "tiller")
    sleep 20
}

_getDependencies() {
    echo "## install infraboxcli"
    pip install infraboxcli

    echo "## Get minio client"
    curl https://dl.minio.io/client/mc/release/linux-amd64/mc > /usr/bin/mc
    chmod +x /usr/bin/mc
}

_portForwardAPI() {
    # Port forward API
    api_pod=$(_getPodName "infrabox-api")

    echo "Port forwarding to API: '$api_pod'"
    kubectl port-forward -n infrabox-system $api_pod 8080 > /dev/null 2>&1 &
    until $(curl --output /dev/null --silent --head --fail http://localhost:8080/ping); do
      >&2 echo "API is unavailable - sleeping"
      sleep 1
    done
}

_deinstallMinio() {
    echo "## Deinstall minio"
    helm delete --purge infrabox-minio || true
}

_installMinio() {
    _deinstallMinio

    echo "## Install minio"
    helm install stable/minio --set serviceType=ClusterIP,replicas=1,persistence.enabled=false -n infrabox-minio --namespace infrabox-system

    # Port forward API
    minio_pod=$(_getPodName "infrabox-minio")
    echo "Port forwarding to minio: '$minio_pod'"
    kubectl port-forward -n infrabox-system $minio_pod 9000 > /dev/null 2>&1 &

    sleep 10

    # init minio client
    mc config host add minio http://localhost:9000 AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY S3v4

    # Create buckets
    mc mb minio/test-infrabox-container-output
    mc mb minio/test-infrabox-project-upload
    mc mb minio/test-infrabox-container-content-cache
    mc mb minio/test-infrabox-docker-registry
    mc ls minio
}

_installInfraboxGCS() {
    _deinstallInfrabox

    echo "## install infrabox"
    master_ip=$(gcloud container clusters describe $cluster_name | grep point | awk '{print $2}')
    echo "Master IP: $master_ip"

    pushd /project/helm/infrabox
    helm install -n infrabox \
        --set general.kubernetes_master=$master_ip \
        --set scheduler.tag="build_$INFRABOX_BUILD_NUMBER" \
        --set docker_registry.auth_tag="build_$INFRABOX_BUILD_NUMBER" \
        --set docker_registry.nginx_tag="build_$INFRABOX_BUILD_NUMBER" \
        --set storage.gcs.enable=true \
        --set storage.s3.enable=false \
        --set api.tag="build_$INFRABOX_BUILD_NUMBER" \
        -f ./values_test.yaml .
    popd

    _portForwardAPI
}

_deinstallInfrabox() {
    echo "## Deinstall infrabox"
    helm delete --purge infrabox || true
}

_installInfraboxMinio() {
    _deinstallInfrabox

    echo "## install infrabox"
    master_ip=$(gcloud container clusters describe $cluster_name | grep point | awk '{print $2}')
    echo "Master IP: $master_ip"

    pushd /project/helm/infrabox
    helm install -n infrabox \
        --set general.kubernetes_master=$master_ip \
        --set scheduler.tag="build_$INFRABOX_BUILD_NUMBER" \
        --set docker_registry.auth_tag="build_$INFRABOX_BUILD_NUMBER" \
        --set docker_registry.nginx_tag="build_$INFRABOX_BUILD_NUMBER" \
        --set storage.gcs.enable=false \
        --set storage.s3.enable=true \
        --set api.tag="build_$INFRABOX_BUILD_NUMBER" \
        -f ./values_test.yaml .
    popd

    _portForwardAPI
}

_clearDatabase() {
    echo "Clear database"
    _sql "DELETE FROM job"
}

_runTestDockerKeepAndPull() {
    pushd "docker_keep"
    echo "## Run test: docker_keep"
    _clearDatabase
    _push
    job_to_pull=$(_sql "SELECT id FROM job WHERE name = 'consumer'")
    job_producer=$(_sql "SELECT id FROM job WHERE name = 'producer'")
    infrabox --host $infrabox_host pull --job-id $job_to_pull --no-container
    ls -al /tmp/infrabox/$job_to_pull/inputs/producer
    cat /tmp/infrabox/$job_to_pull/inputs/producer/data.txt
    popd
}

_runTests() {
    _runTestDockerKeepAndPull

    pushd tests
    tests.sh
    popd
}

_getDependencies
_createCluster
_installMinio

# Test with GCS
_installPostgres
_installInfraboxGCS
_runTests

# Stop all port forwardings
killall kubectl

# Test with S3
_installPostgres
_installInfraboxMinio
_runTests

echo "## Finished"
