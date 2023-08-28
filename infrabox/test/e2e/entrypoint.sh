#!/bin/bash -ev

IMAGE_TAG=build_$INFRABOX_BUILD_NUMBER

_prepareKubectl() {
    echo "## Prepare kubectl"

	SERVICE_NAME="e2e-cluster"

    CA_CRT="/var/run/infrabox.net/services/$SERVICE_NAME/ca.crt"

    ENDPOINT=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/endpoint)
    TOKEN=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/token)

    kubectl config set-cluster $SERVICE_NAME \
        --server=$ENDPOINT \
        --embed-certs=true \
        --certificate-authority=$CA_CRT

    kubectl config set-credentials admin \
        --token=$TOKEN

    kubectl config set-context default-system \
        --cluster=$SERVICE_NAME \
        --user=admin

    kubectl config use-context default-system

    kubectl get pods

    kubectl config use-context default-system

    kubectl get nodes
}

_createNamesapce() {
    echo "## create infrabox namespace"
    
    kubectl create ns infrabox-worker
    kubectl create ns infrabox-system
}

_getNginxIP() {
    external_ip=""
    while [ -z $external_ip ]; do
        external_ip=$(kubectl -n kube-system get svc nic-nginx-ingress-controller --template="{{range .status.loadBalancer.ingress}}{{.ip}}{{end}}")
        [ -z "$external_ip" ] && sleep 10
    done

    echo $external_ip
}

_initHelm() {
    echo "## init helm"

    helm repo add stable https://charts.helm.sh/stable
    helm repo add bitnami https://charts.bitnami.com/bitnami
}

_getPodNameImpl() {
    kubectl get pods -n $1 | grep $2 | grep Running | awk '{print $1}'
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

_installPostgres() {
    echo "## Install postgres"
    # postgres 15 will have the problem of "SCRAM authentication requires libpq version 10 or above"
    # which may need to update base image OS version...
	helm install postgres oci://registry-1.docker.io/bitnamicharts/postgresql \
        --version 12.5.1 \
		--set auth.postgresPassword=postgres \
        --set image.tag=13.11.0-debian-11-r0 \
		--wait \
        --namespace infrabox-system

    # Wait until postgres is ready
    postgres_pod=$(_getPodName "infrabox-system" "postgres")
    echo "Port forwarding to postgres: '$postgres_pod'"
    kubectl port-forward -n infrabox-system $postgres_pod 5432 &

    # Wait until postgres is ready
    until psql postgresql://postgres:postgres@localhost:5432 -c '\l'; do
        >&2 echo "Postgres is unavailable - sleeping"
        sleep 1
	done
}

_installMinio() {
    echo "## Install minio"

    helm install \
        infrabox-minio \
        --set service.type=ClusterIP,replicas=1,persistence.enabled=false \
        --namespace infrabox-system \
        --wait \
        stable/minio
}

_installNginxIngress() {
    echo "## Install nginx ingress"

    helm install \
        nic \
        --namespace kube-system \
        --wait \
        bitnami/nginx-ingress-controller

    nginx_ip=$(_getNginxIP)

    export ROOT_URL="$nginx_ip.nip.io"
    echo "Generating certs for: $ROOT_URL"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /tmp/tls.key -out /tmp/tls.crt -subj "/CN=$ROOT_URL"

    kubectl create -n infrabox-system secret tls infrabox-tls-certs --key /tmp/tls.key --cert /tmp/tls.crt
}

_installInfrabox() {
	cd /infrabox/context/deploy/infrabox

    ssh-keygen -N '' -t rsa -f id_rsa
    ssh-keygen -f id_rsa.pub -e -m pem > id_rsa.pem

    mkdir -p /var/run/secrets/infrabox.net/rsa/
    cp id_rsa* /var/run/secrets/infrabox.net/rsa/

    echo "## Install infrabox"

    PW=ouRGa4RGDM9FLr09Y21K4yL9hAg8eg1C

	cat >my_values.yaml <<EOL
admin:
  email: admin@admin.com
  password: $PW
  private_key: $(base64 -w 0 ./id_rsa)
  public_key: $(base64 -w 0 ./id_rsa.pem)
general:
  dont_check_certificates: true
  log_level: debug
database:
  postgres:
    db: postgres
    enabled: true
    host: postgres-postgresql.infrabox-system
    password: postgres
    username: postgres
host: $ROOT_URL
image:
  tag: $IMAGE_TAG
storage:
  s3:
    # these are the default accessKey/secretKey defined in the helm chart
    access_key_id: AKIAIOSFODNN7EXAMPLE
    bucket: infrabox
    enabled: true
    endpoint: infrabox-minio.infrabox-system
    port: '9000'
    region: us-east1
    secret_access_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    secure: false
job:
    docker_daemon_config: |-
        {"insecure-registries": ["$ROOT_URL"]}
EOL

    helm install --namespace infrabox-system -f my_values.yaml --wait --timeout=20m infrabox .

    kubectl -n infrabox-system port-forward service/infrabox-api 8080 &

    export INFRABOX_ROOT_URL=http://localhost:8080
    export INFRABOX_ADMIN_EMAIL=admin@admin.com
    export INFRABOX_ADMIN_PASSWORD=$PW
}

_runTests() {
    echo "## Run tests"
    pushd /infrabox/context/infrabox/test/e2e

    set +e
    pytest e2e.py -n 8
    rc=$?

    exit $rc
}

main() {
    _prepareKubectl
    _createNamesapce
    _initHelm
    _installPostgres
    _installMinio
    _installNginxIngress
    _installInfrabox
    _runTests
}

main
