# Local development with docker-compose
This setup is not meant for production. You may use it to try InfraBox or use it for local development.

## Prerequisites
- [infraboxcli](https://github.com/infrabox/cli)
- [mc](https://docs.minio.io/docs/minio-client-quickstart-guide)
- [docker-compose](https://docs.docker.com/compose/)

## Build docker contaienrs
See [these instructions](build_images.md) on how to build the InfraBox docker containers.

## Generate docker-compose.yaml
InfraBox comes with deploy/install.py which can generate for you a docker-compose.yaml with all the neccessary configuration values to get started quickly.

    $ python deploy/install.py \
        -o /tmp/compose \
        --platform docker-compose
        --docker-registry <YOUR_REGISTRY>
        --account-signup-enabled

Set <YOUR\_REGISTRY> to the same value you used for building the images in the previous step. This command creates a default configuration for InfraBox. You may want to configure additional things like

TODO: Support them:
- [gerrit](configure/gerrit.md)
- [github](configure/github.md)
- [ldap](configure/ldap.md)

## Start it
Before you start make sure you don't have a local postgres database running. The docker-compose setup uses host networking and the postgres database used by InfraBox will use postgres default port 5432. During startup you may see a few errors, because the database hasn't been initialized yet. You may ignore them.

    $ cd <OUTPUT_DIR>
    $ docker-compose up

Now all services should start up. After database migration has been finished successfully you have start another shell and run

    $ cd <OUTPUT_DIR>
    $ ./init.sh

This will create all the neccessary buckets in minio. Now you are ready to go an can point your browser to

    http://localhost:30201

To access the InfraBox dashboard. The default configuration will use the following ports for the different services

|Service        |Adress                |
|---------------|----------------------|
|API            |http://localhost:30200|
|Dashboard      |http://localhost:30201|
|Docker Registry|http://localhost:30202|
|Docs           |http://localhost:30203|

## Differences to kubernetes setup
For docker-compose a different scheduler has been implemented. Currently it does not run jobs in parallel. So all your jobs a executed sequentially using your host docker daemon.
