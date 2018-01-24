# <a href="http://infrabox.net"><img src="src\dashboard-client\static\logo_compact_transparent.png" width="200"></a> [![Build Status](https://infrabox.ninja/api/v1/projects/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/state.svg?branch=master)](https://infrabox.ninja/dashboard/#/project/infrabox)

InfraBox is a serverless computing platform focusing on efficiently executing build and test workflows for your project. You may execute everything on InfraBox which runs in a docker container. Some of InfraBox features include:

- [Static and dynamic workflows](https://infrabox.ninja/docs/#dynamic-workflows)
- [Set resource limits (CPU and memory) for each task](https://infrabox.ninja/docs/#workflow-config)
- [GitHub integration](docs/configure/github.md)
- [Gerrit integration](docs/configure/gerrit.md)
- GitLab (comming soon)
- [LDAP support](docs/configure/ldap.md)
- [and many more](http://infrabox.net)

## Want to see it in action?
InfraBox is built on InfraBox. See all the builds [here](https://infrabox.ninja/dashboard/#/project/infrabox).

## You want to try it for free?
Have a look at the InfraBox playground [https://infrabox.ninja/](https://infrabox.ninja/dashboard/#/login).
It's a hosted version of InfraBox. You can use it for free with up to 1 CPU and 1024MB per job.

Quickstart Guides:
- [Connect your github repository](docs/guides/connect_github.md)
- [Upload a workflow (you don't need a git repository)](docs/guides/upload.md)

## Install InfraBox
You have multiple options to install InfraBox:

- [Docker Compose](docs/install_docker_compose.md)
- [Kubernetes Engine (Google Cloud)](docs/install_gcloud.md)

## Contact
Follow us on Twitter: [@Infra_Box](https://twitter.com/Infra_Box) or have look at our Slack channel [infrabox.slack.com](https://infrabox.slack.com/).

|Component|Coverage|
|---------|--------|
|github-api|[![coverage](https://infrabox.ninja/api/v1/projects/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=ib/test/github-api)](https://infrabox.ninja/dashboard/#/project/infrabox)|
|github-review|[![coverage](https://infrabox.ninja/api/v1/projects/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=ib/test/github-review)](https://infrabox.ninja/dashboard/#/project/infrabox)|
|pyinfrabox|[![coverage](https://infrabox.ninja/api/v1/projects/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=ib/test/pyinfrabox)](https://infrabox.ninja/dashboard/#/project/infrabox)|
|registry-auth|[![coverage](https://infrabox.ninja/api/v1/projects/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=ib/test/registry-auth)](https://infrabox.ninja/dashboard/#/project/infrabox)|
