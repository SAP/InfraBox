# Local development with docker-compose
This setup is not meant for production. You may use it to try InfraBox or use it for local development.

For docker-compose a different scheduler has been implemented. Currently it does not run jobs in parallel. So all your jobs a executed sequentially using your host docker daemon.

The default configuration starts its own postgres a minio for storing you data. So if you delete the volume your data is lost. You may configure and external s3/minio or postgresql database.

## Prerequisites
- [docker](https://www.docker.com/)
- [docker-compose](https://docs.docker.com/compose/)

## Clone repository

    $ git clone https://github.com/InfraBox/infrabox.git infrabox
    $ cd infrabox

## Generate docker-compose.yaml
InfraBox comes with deploy/install.py which can generate for you a docker-compose.yaml with all the neccessary configuration values to get started quickly.

    $ python deploy/install.py \
        -o /tmp/compose \
        --platform docker-compose

You are not ready to startup InfraBox

    $ cd /tmp/compose/compose
    $ docker-compose up


## Configure additional components
- [external postgres](configure/postgres.md)
- [ldap](configure/ldap.md)

Not yet supported:
- [gerrit](configure/gerrit.md)
- [github](configure/github.md)
- [external s3](configure/s3.md)
