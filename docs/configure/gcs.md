# Google Cloud Storage
Instead of using S3 API compatible storage you may also use GCS. To use it you have to create a service account with the right permissions to read and write to GCS.

## Create service account
1. Login to GCP Console and go to IAM -> Service accounts
2. Click on "Create service account" and give it a  name
3. Select the role "Storage Admin"
4. Select "Furnish a new private key" and select JSON as key type
5. Click on create

A .json file with the service account's credentials will be downloaded. Keep this at a safe place.

## Create buckets
InfraBox requires you to have 4 buckets created. As bucket names have to be globally unique you have to chose available names for the four buckets:

- container-output
- project-upload
- container-content-cache
- docker-registry

You have to create them before installing InfraBox. 

## Configure
When configuring the InfraBox installation with install.py use these options

    --storage gcs
    --gcs-project-id <YOUR_GCP_PROJECT_ID>
    --gcs-service-account-key-file <PATH_TO_THE_SERVICE_ACCOUNT_KEY_FILE>
    
Set the bucket names which you have create in the previous step:

    --gcs-container-output-bucket <NAME>
    --gcs-project-upload-bucket <NAME>
    --gcs-container-content-cache-bucket <NAME>
    --gcs-docker-registry-bucket <NAME>
