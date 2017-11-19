# <img src="src\dashboard-client\static\logo_compact_transparent.png" width="200"> [![Build Status](https://infrabox.ninja/api/cli/v1/project/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/build/state.svg?branch=master)](https://demo.infrabox.net/dashboard/project/e8a9bf87-10c8-41fa-b632-f6bb40d0d14e)

|Component|Coverage|
|---------|--------|
|github-api|[![coverage](https://infrabox.ninja/api/cli/v1/project/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=test/github-api&branch=master)](https://infrabox.ninja/dashboard/#/project/infrabox)|
|github-review|[![coverage](https://infrabox.ninja/api/cli/v1/project/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=test/github-api&branch=master)](https://infrabox.ninja/dashboard/#/project/infrabox)|
|pyinfrabox|[![coverage](https://infrabox.ninja/api/cli/v1/project/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=test/pyinfrabox&branch=master)](https://infrabox.ninja/dashboard/#/project/infrabox)|

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

## Contact
Follow us on Twitter: [@Infra_Box](https://twitter.com/Infra_Box) or have look at our Slack channel [infrabox.slack.com](https://infrabox.slack.com/).
