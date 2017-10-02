# CloudSQL Postgres
This is a quick walkthrough on how to create a cloudsql postgres database to be used with InfraBox.

## Create an instance
See [here](https://cloud.google.com/sql/docs/postgres/create-instance) for a description on how to create a postgres instances.

Remember your postgres password. You'll need it in a later step.

## Create a database
See [here](https://cloud.google.com/sql/docs/postgres/create-manage-databases) for a description on hwo to create a database in postgres.

You may use infrabox as name for your database.

## Connect from Google Container Engine
InfraBox runs on Google Container Engine. To be able to connect from GKE to your cloudsql postgres database you have to follow [these](https://cloud.google.com/sql/docs/postgres/connect-container-engine) instructions until Step 4. The InfraBox instllation will take care of step 5 to 7 for you.

After those steps you should have downloaded a .json file containing your service accounts private key, create a password for your proxy user and figured our  your instance connection name. All these things are required for the InfraBox installation.

# Google Cloud Storage

You need a service account for GCS. See [here](https://cloud.google.com/storage/docs/authentication) on how to create one. Select role "Storage Admin" for your service account. Download the json file and use it later during installation.

You have to create the following buckets before installing InfraBox:

- infrabox-container-content-cache
- infrabox-project-upload
- infrabox-container-output
- infrabox-docker-registry
