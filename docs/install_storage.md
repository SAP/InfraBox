# Install Storage
InfraBox requires some S3-like storage.

## Use S3 compatible storage
So if you already have S3 compatible storage you may just go ahead and create the necessary secrets:

Create for namespace infrabox-system AND infrabox-worker.

    kubectl -n <NAMESPACE> create secret generic \
        infrabox-s3-credentials \
        --from-literal=accessKey=<ACCESS_KEY> \
        --from-literal=secretKey=<SECRET_KEY>

For the helm configuration you have to set the following values:

        storage.gcs.enabled=false
        storage.s3.enabled=true
        storage.s3.region=<REQUIRED>
        storage.s3.endpoint=<REQUIRED>

        # The buckets must exist
        storage.s3.container_output_bucket=infrabox-container-output
        storage.s3.project_upload_bucket=infrabox-project-upload
        storage.s3.container_content_cache_bucket=infrabox-container-content-cache
        storage.s3.docker_registry_bucket=infrabox-docker-registry

        # Optional values
        # storage.s3.port=443
        # storage.s3.secure=true

Make sure you created the buckets.

## Use Google Cloud storage
Create a service account for GCS with read/write permissions (Storage Object Admin).
Download the json file and create the secret like below.

Create for namespace infrabox-system AND infrabox-worker.

    kubectl -n <NAMESPACE> create secret generic \
        infrabox-gcs \
        --from-file=gcs_service_account.json=[SERVICE_ACCOUNT_FILE_PATH]

For the helm configuration you have to set the following values:

        storage.s3.enabled=false
        storage.gcs.enabled=true
        storage.gcs.project_id=<REQUIRED>

        # The buckets must exist
        storage.gcs.container_output_bucket=infrabox-container-output
        storage.gcs.project_upload_bucket=infrabox-project-upload
        storage.gcs.container_content_cache_bucket=infrabox-container-content-cache
        storage.gcs.docker_registry_bucket=infrabox-docker-registry

Make sure you created the buckets.

## Use minio
Minio is a S3 compatible storage which you can run yourself in your cluster.
The following instructions are not meant for a production ready setup. You may use it to get started with InfraBox. See the minio documentation on how to setup a production ready cluster.

	helm install stable/minio \
		--set serviceType=ClusterIP,replicas=1,persistence.enabled=false \
		-n infrabox-minio \
		--namespace infrabox-system

We also have to create the buckets in minio

    kubectl port-forward <MINIO_POD_NAME> -n infrabox-system 9000

    curl https://dl.minio.io/client/mc/release/linux-amd64/mc > mc
    chmod +x mc

    ./mc config host add minio http://localhost:9000 AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY S3v4

    ./mc mb minio/infrabox-container-output
    ./mc mb minio/infrabox-project-upload
    ./mc mb minio/infrabox-container-content-cache
    ./mc mb minio/infrabox-docker-registry
    ./mc ls minio

The default credentials are:

    AccessKey: AKIAIOSFODNN7EXAMPLE
    SecretKey: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

See [TODO] how to configure the credentials for S3 compatible storage.
