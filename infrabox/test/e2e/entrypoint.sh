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
    git clone https://github.com/SAP/InfraBox-cli.git /cli
    pushd /cli
    pip install -e .
    infrabox version
    git rev-parse HEAD
    popd
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

    kubectl -n kube-system create sa tiller
    kubectl create clusterrolebinding tiller \
		--clusterrole cluster-admin \
		--serviceaccount=kube-system:tiller
    helm init --service-account tiller --wait

    helm repo add stable https://charts.helm.sh/stable
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
	helm install -n postgres stable/postgresql \
        --version 1.0.0 \
		--set imageTag=9.6.2,postgresPassword=postgres,probes.readiness.periodSeconds=5 \
		--wait \
        --namespace infrabox-system

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
        --wait \
        stable/minio
}

_installNginxIngress() {
    echo "## Install nginx ingress"

    helm install \
        -n nic \
        --namespace kube-system \
        --wait \
        stable/nginx-ingress

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

    PW=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

	cat >my_values.yaml <<EOL
admin:
  email: admin@admin.com
  password: $PW
  private_key: $(base64 -w 0 ./id_rsa)
  public_key: $(base64 -w 0 ./id_rsa.pem)
general:
  dont_check_certificates: true
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

    helm install --namespace infrabox-system -f my_values.yaml --wait .

    export INFRABOX_DATABASE_HOST=localhost
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
