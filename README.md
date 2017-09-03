# InfraBox

## Requirements

- Kubernetes 1.6
- Postgres 9.6
- S3 compatible storage (i.e. minio)

## Build Containers
To build the container you need to have installed:

- [infraboxcli](https://github.com/infrabox/cli)
- [docker](https://www.docker.com/)

To run Infrabox you first have to build all its docker containers. To do so run

    ./deploy/build.sh <YOUR_DOCKER_REGISTRY>
    ./deploy/push.sh <YOUR_DOCKER_REGISTYR>

i.e.:

    ./deploy/build.sh 192.168.157.129:5000/
    ./deploy/push.sh 192.168.157.129:5000/

Now you have all the containers build and your registry. Next step is to setup all the necessary credentials for running InfraBox in your kubernetes cluster.

## Try it on minikube
See [this guide](docs/development.md) How to get InfraBox quickly setup on your local machine with the help of minikube.

## Setup Components
Depending on the environment you would like to run InfraBox in you have to setup:

1. [Setup kubernetes](docs/install_kubernetes.md)
2. [Setup postgresql](docs/install_postgres.md)
3. [Setup storage](docs/install_storage.md)
4. [Setup docker registry](docs/install_docker_registry.md)
5. [Setup InfraBox](docs/install_infrabox.md)

Optionally you way want to configure:
- [Setup gerrit](docs/install_gerrit.md)
- [Setup github](docs/install_github.md)
- [Setup ldap](docs/install_ldap.md)
