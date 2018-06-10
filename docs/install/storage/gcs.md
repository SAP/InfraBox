# Google Cloud Storage
Instead of using S3 API compatible storage you may also use GCS. To use it you have to create a service account with the right permissions to read and write to GCS.

## Create service account
1. Login to GCP Console and go to "IAM & Admin" -> "Service accounts"
2. Click on "Create service account" and give it a  name
3. Select the role "Storage Admin"
4. Select "Furnish a new private key" and select JSON as key type
5. Click on create

A .json file with the service account's credentials will be downloaded. Keep this at a safe place.

## Create buckets
InfraBox requires you to have one bucket created. As bucket names have to be globally unique you have to chose an available name for the bucket. You have to create them before installing InfraBox.

When installing with `helm` later on set these options:

```yaml
storage:
    gcs:
        # Enable google cloud storage
        enabled: true

        # Bucket name
        bucket: # <REQUIRED>

        # base64 encoded service account .json file
        service_account: # <REQUIRED>
```
