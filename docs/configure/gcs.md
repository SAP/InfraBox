# Google Cloud Storage
Current GCS can only be used if you run InfraBox on GKE.

    --storage gcs
    --gcs-project-id <YOUR_PROJECT_ID>

InfraBox will create a few buckets with default names. You may change the names with:

    --gcs-container-output-bucket <NAME>
    --gcs-project-upload-bucket <NAME>
    --gcs-container-content-cache-bucket <NAME>
    --gcs-docker-registry-bucket <NAME>


