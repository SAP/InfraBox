# <img src="src\dashboard-client\static\logo_compact_transparent.png" width="200"> [![Build Status](https://infrabox.ninja/api/cli/v1/project/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/build/state.svg?branch=master)](https://infrabox.ninja/dashboard/#/project/infrabox)

InfraBox is a serverless computing platform focusing on efficiently executing build and test workflows for your project. You may execute everything on InfraBox which runs in a docker container. Some of InfraBox features include:

- Static and dynamic workflows
- Set resource limits (CPU and memory) for each task
- GitHub integration
- Gerrit integration
- LDAP support
- and many more

## You want to try it?
Have a look at the InfraBox playground: [https://infrabox.ninja/](https://infrabox.ninja/)

## Install InfraBox
You have multiple options to install InfraBox.

- [Docker Compose](docs/install_docker_compose.md)
- [Kubernetes Engine (Google Cloud)](docs/install_gcloud.md)
- Your own Kubernetes Cluster

## Contact
Follow us on Twitter: [@Infra_Box](https://twitter.com/Infra_Box) or have look at our Slack channel [infrabox.slack.com](https://infrabox.slack.com/).

|Component|Coverage|
|---------|--------|
|github-api|[![coverage](https://infrabox.ninja/api/cli/v1/project/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=ib/test/github-api)](https://infrabox.ninja/dashboard/#/project/infrabox)|
|github-review|[![coverage](https://infrabox.ninja/api/cli/v1/project/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=ib/test/github-review)](https://infrabox.ninja/dashboard/#/project/infrabox)|
|pyinfrabox|[![coverage](https://infrabox.ninja/api/cli/v1/project/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=ib/test/pyinfrabox)](https://infrabox.ninja/dashboard/#/project/infrabox)|
