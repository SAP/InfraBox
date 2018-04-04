#!/bin/sh -e

# Checks
command -v kubectl >/dev/null 2>&1 || { echo >&2 "kubectl not found.  Aborting."; exit 1; }
command -v mc >/dev/null 2>&1 || { echo >&2 "mc not found.  Aborting."; exit 1; }

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

_installMinio() {
	echo "Installing minio"
	echo "WARNING: THIS IS NOT FOR PRODUCTION USE"
	helm install stable/minio \
		--set serviceType=ClusterIP,replicas=1,persistence.enabled=false \
		-n infrabox-minio \
		--namespace infrabox-system

	s3_access_key="AKIAIOSFODNN7EXAMPLE"
	s3_secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

   	# Port forward API
	minio_pod=$(_getPodName "infrabox-minio")
	echo "Port forwarding to minio: '$minio_pod'"
	killall kubectl || true
	sleep 5
	kubectl port-forward -n infrabox-system $minio_pod 9000 &
	sleep 5

	mc config host add infrabox-minio http://localhost:9000 $s3_access_key $s3_secret_key S3v4

	mc mb infrabox-minio/infrabox-container-output
	mc mb infrabox-minio/infrabox-project-upload
	mc mb infrabox-minio/infrabox-container-content-cache
	mc mb infrabox-minio/infrabox-docker-registry
	mc ls infrabox-minio
}

_install() {
	kubectl create namespace infrabox-system || true
	kubectl create namespace infrabox-worker || true
	_installMinio

    echo "When installing infrabox use:"
    echo "  --s3-access-key=$s3_access_key"
    echo "  --s3-secret-key=$s3_secret_key"
    echo "  --s3-port=9000"
    echo "  --s3-endpoint=infrabox-minio.infrabox-system"
    echo "  --s3-secure=false"
    echo "  --s3-region=us-east-1"
}

_install
