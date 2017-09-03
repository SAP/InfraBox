#!/bin/sh -e

install_minio=true
install_postgres=false

# Values file
values_yaml="values_ccloud.yaml"

# Leave it empty if install_minio=true
s3_access_key=""
s3_secret_key=""

# Leave it empty if install_postgres=true
postgres_username="infrabox"
postgres_password="0vVtLmA9T6u6Q19g"

registry_admin_username="admin" # Required
registry_admin_password="admin" # Required

github_client_id="$INFRABOX_LOCAL_GITHUB_CLIENT_ID"
github_client_secret="$INFRABOX_LOCAL_GITHUB_CLIENT_SECRET"
github_webhook_secret=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

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

_installPostgres() {
	echo "Installing postgres"
	echo "WARNING: THIS IS NOT FOR PRODUCTION USE"

	cd infrabox-postgres
	helm install -n infrabox-postgres -f $values_yaml .

	postgres_password="postgres"
	postgres_username="postgres"

	cd ..
}

_installInfraBox() {
	cd infrabox
	helm install -n infrabox -f $values_yaml .

	cd ..
}

_installSecrets() {
	# Setup S3 credentials
	if kubectl describe secret -n infrabox-system infrabox-s3-credentials > /dev/null 2>&1; then
		echo "secret infrabox-s3-credentials already exists. Not creating it again."
	else
		kubectl -n infrabox-system create secret generic \
			infrabox-s3-credentials \
			--from-literal=accessKey=$s3_access_key \
			--from-literal=secretKey=$s3_secret_key
	fi

	if kubectl describe secret -n infrabox-system infrabox-s3-credentials > /dev/null 2>&1; then
		echo "secret infrabox-s3-credentials already exists. Not creating it again."
	else
		kubectl -n infrabox-worker create secret generic \
			infrabox-s3-credentials \
			--from-literal=accessKey=$s3_access_key \
			--from-literal=secretKey=$s3_secret_key
	fi

	if kubectl describe secret -n infrabox-system infrabox-dashboard > /dev/null 2>&1; then
		echo "secret infrabox-dashboard already exists. Not creating it again."
	else
        kubectl -n infrabox-system create secret generic \
            infrabox-dashboard \
            --from-literal=secret=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
    fi

	# Setup postgres credentials
	if [ "$install_postgres" != true ]; then
		if kubectl describe secret -n infrabox-system infrabox-postgres-db-credentials > /dev/null 2>&1; then
			echo "secret infrabox-postgres-db-credentials already exists. Not creating it again."
		else
			kubectl -n infrabox-system create secret generic \
				infrabox-postgres-db-credentials \
				--from-literal=username=$postgres_username \
				--from-literal=password=$postgres_password
		fi

		if kubectl describe secret -n infrabox-worker infrabox-postgres-db-credentials > /dev/null 2>&1; then
			echo "secret infrabox-postgres-db-credentials already exists. Not creating it again."
		else

			kubectl -n infrabox-worker create secret generic \
				infrabox-postgres-db-credentials \
				--from-literal=username=$postgres_username \
				--from-literal=password=$postgres_password
		fi
	fi

	# Setup docker registry credentials

	if kubectl describe secret -n infrabox-system infrabox-docker-registry > /dev/null 2>&1; then
		echo "secret infrabox-docker-registry already exists. Not creating it again."
	else
		kubectl -n infrabox-worker create secret generic \
			infrabox-docker-registry \
			--from-literal=username=$registry_admin_username \
			--from-literal=password=$registry_admin_password
	fi

	if kubectl describe secret -n infrabox-system infrabox-docker-registry > /dev/null 2>&1; then
		echo "secret infrabox-docker-registry already exists. Not creating it again."
	else
		kubectl -n infrabox-system create secret generic \
			infrabox-docker-registry \
			--from-literal=username=$registry_admin_username \
			--from-literal=password=$registry_admin_password
	fi

	# Setup github credentials
	if kubectl describe secret -n infrabox-system infrabox-github > /dev/null 2>&1; then
		echo "secret infrabox-github already exists. Not creating it again."
	else
		kubectl -n infrabox-system create secret generic \
			infrabox-github \
			--from-literal=client_id=$github_client_id \
			--from-literal=client_secret=$github_client_secret \
			--from-literal=webhook_secret=$github_webhook_secret
	fi
}

_install() {
	kubectl create namespace infrabox-system || true
	kubectl create namespace infrabox-worker || true

	if [ "$install_minio" = true ]; then
		_installMinio
	fi

	if [ "$install_postgres" = true ]; then
		_installPostgres
	fi

	_installSecrets
	_installInfraBox
}

_install
