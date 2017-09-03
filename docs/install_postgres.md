# Setup postgres
InfraBox requires a Postgres database in version 9.6. You may either run you own database or use Google Cloud SQL.

## Setup with Google Cloud SQL
See https://cloud.google.com/sql/docs/postgres/connect-container-engine.

When installing InfraBox with helm you have to set the following configuration values:

    storage.postgres.enabled=false
    storage.cloudsql.enabled=true
    storage.cloudsql.instance_connection_name=<INSTANCE_CONNECTION_NAME>

InfraBox will the use Cloud SQL's proxy which always runs on localhost (within the PODs).
So make sure you don't change postgres settings. They should look like this (default values):

    storage.postgres.host=localhost
    storage.postgres.port=5432

    # You may change the db
    # storage.postgres.db=infrabox


Additionally you have to create a kubernetes secret with the username and password:
Create for namespace infrabox-system AND infrabox-worker.

    kubectl -n <NAMESPACE> create secret generic \
        infrabox-cloudsql-instance-credentials \
        --from-file=credentials.json=[PROXY_KEY_FILE_PATH]

    kubectl -n <NAMESPACE> create secret generic \
        infrabox-cloudsql-db-credentials \
        --from-literal=username=<PROXY_USER> \
        --from-literal=password=<PROXY_PASSWORD>


## Setup with regular postgres
When installing InfraBox with helm you have to set the following configuration values:

    storage.cloudsql.enabled=false
    storage.postgres.enabled=true
    storage.postgres.host=<HOSTNAME>
    # storage.postgres.port=5432
    # storage.postgres.db=infrabox

Additionally you have to create a kubernetes secret with the username and password:
Create for namespace infrabox-system AND infrabox-worker.

    kubectl -n <NAMESPACE> create secret generic \
        infrabox-postgres-db-credentials \
        --from-literal=username=<USER> \
        --from-literal=password=<PASSWORD>

# Create schema
After creating setting up the database you have to initialize the database. For this use:

    psql < src/postgres/schema_production.sql
