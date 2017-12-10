# Local development with docker-compose
This setup is not meant for production. You may use it to try InfraBox or use it for local development.

For docker-compose a different scheduler has been implemented. Currently it does not run jobs in parallel. So all your jobs are executed sequentially using your host docker daemon.

The default configuration starts its own postgres a minio for storing your data. If you delete the volume your data is lost. You may configure and external s3/minio or postgresql database.

## Prerequisites
- [docker](https://www.docker.com/)
- [docker-compose](https://docs.docker.com/compose/)

## Clone repository

    $ git clone https://github.com/InfraBox/infrabox.git infrabox
    $ cd infrabox

## Generate RSA Key
InfraBox uses a RSA key to sign certain information for security reasons. You need to generate a RSA key and keep it at a secure place

    $ ssh-keygen -N '' -t rsa -f id_rsa
    $ ssh-keygen -f id_rsa.pub -e -m pem > id_rsa.pem

## Generate docker-compose.yaml
InfraBox comes with deploy/install.py which can generate docker-compose.yaml with all the neccessary configuration values.

    $ python deploy/install.py \
        -o /tmp/compose \
        --general-rsa-public-key ./id_rsa.pem \
        --general-rsa-private-key ./id_rsa \
        --platform docker-compose

You are now ready to startup InfraBox

    $ cd /tmp/compose/compose
    $ docker-compose up

After it started up successfully you may start [pushing workflows](./guides/upload.md) to it.

## Configure additional components
- [external postgres](configure/postgres.md)
- [ldap](configure/ldap.md)

Not yet supported:
- [gerrit](configure/gerrit.md)
- [github](configure/github.md)
- [external s3](configure/s3.md)
