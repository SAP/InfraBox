#!/bin/bash -e

# K3s must be already running and kubectl configured

ROOT_URL='192-168-232-130.nip.io'
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

_initHelm() {
    echo "## init helm"
    kubectl -n kube-system create sa tiller --dry-run -o yaml | kubectl apply -f -
    kubectl create clusterrolebinding tiller \
		--clusterrole cluster-admin \
		--serviceaccount=kube-system:tiller \
        --dry-run -o yaml | kubectl apply -f -
    helm init --service-account tiller --wait
}

_installPostgres() {
    echo "## Install postgres"
	helm install -n postgres stable/postgresql \
        --version 1.0.0 \
		--set imageTag=9.6.2,postgresPassword=postgres,probes.readiness.periodSeconds=5 \
		--wait \
        --namespace infrabox-system
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
        --set controller.service.type=NodePort \
        --set controller.service.nodePorts.https=30443 \
        stable/nginx-ingress

    if [ ! -f /tmp/tls.key ]; then
        echo "Generating certs for: $ROOT_URL"
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /tmp/tls.key -out /tmp/tls.crt -subj "/CN=$ROOT_URL"
        kubectl create -n infrabox-system secret tls infrabox-tls-certs --key /tmp/tls.key --cert /tmp/tls.crt --dry-run -o yaml | kubectl apply -f -
    fi
}

_installInfrabox() {
    kubectl create ns infrabox-worker --dry-run -o yaml  | kubectl apply -f -
    kubectl create ns infrabox-system --dry-run -o yaml  | kubectl apply -f -

    pushd deploy/infrabox

    if [ ! -f /tmp/id_rsa ]; then
        ssh-keygen -N '' -t rsa -f /tmp/id_rsa
        ssh-keygen -f /tmp/id_rsa.pub -e -m pem > /tmp/id_rsa.pem
    fi

    echo "## Install infrabox"
	cat >/tmp/my_values.yaml <<EOL
port: 30443
admin:
  email: admin@admin.com
  password: Admin123!
  private_key: $(base64 -w 0 /tmp/id_rsa)
  public_key: $(base64 -w 0 /tmp/id_rsa.pem)
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
  repository: localhost:5000/infrabox
  tag: latest
storage:
  s3:
    access_key_id: AKIAIOSFODNN7EXAMPLE
    bucket: infrabox
    enabled: true
    endpoint: infrabox-minio.infrabox-system
    port: '9000'
    region: us-east-1
    secret_access_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    secure: false
job:
    docker_daemon_config: |-
        {"insecure-registries": ["$ROOT_URL"]}
account:
    signup:
        enabled: true
api:
    replicas: 1
dev:
  enabled: true
  repo_path: $DIR
EOL
    helm install --namespace infrabox-system -f /tmp/my_values.yaml --name infrabox --wait .
    popd
}

main() {
    #_initHelm
    #_installPostgres
    #_installMinio
    #_installNginxIngress
    _installInfrabox
}

main
