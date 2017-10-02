# InfraBox
InfraBox is a serverless computing platform focusing on efficiently executing build and test workflows for your project. You may execute everything on InfraBox which runs in a docker container. Some of InfraBox features include:

- Static and dynamic workflows
- Set resource limits (CPU and memory) for each task
- GitHub integration
- Gerrit integration
- LDAP support
- and many more

## Requirements

- Kubernetes 1.7
- Postgres 9.6
- S3 compatible storage (i.e. minio)

## Install InfraBox
You have multiple options to install InfraBox.

- [Docker Compose](docs/install_docker_compose.md)
- [Minikube](docs/install_minikube.md)
- [On your own Kubernetes cluster](docs/install_kubernetes.md)
