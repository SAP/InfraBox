# <a href="http://infrabox.net"><img src="src\dashboard-client\static\logo_compact_transparent.png" width="200"></a> [![Build Status](https://infrabox.ninja/api/v1/projects/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/state.svg?branch=master)](https://infrabox.ninja/dashboard/#/project/infrabox)

InfraBox is a continuous integration system. It's well suited for cloud native applications and has [native support for kubernetes](https://github.com/InfraBox/examples/tree/master/kubernetes). Watch our short introduction video:

[![Introduction to InfraBox](https://img.youtube.com/vi/O8N2U7d404I/0.jpg)](https://www.youtube.com/watch?v=O8N2U7d404I)

Some of InfraBox' features are:

- [Static and dynamic workflows](https://github.com/InfraBox/examples)
- [Set resource limits (CPU and memory) for each task](https://github.com/InfraBox/examples)
- [GitHub integration](docs/configure/github.md)
- [Gerrit integration](docs/configure/gerrit.md)
- GitLab (comming soon)
- [LDAP support](docs/configure/ldap.md)
- [and many more, see our examples](https://github.com/InfraBox/examples)

## Want to see it in action?
InfraBox is built on InfraBox. See all the builds [here](https://infrabox.ninja/dashboard/#/project/infrabox).

## Install InfraBox
You have multiple options to install InfraBox:

- [Docker Compose (For local testing)](docs/install_docker_compose.md)
- [Kubernetes Engine (GCP, Deployment Manager)](deploy/gcp/deployment_manager/)
- [Kubernetes Engine (GCP, manual configuration)](docs/install_gcloud.md)

## Contribute
Any contribute is highly appreciated. See our [developer's documentation](docs/dev.md) for details.

## Contact
Follow us on Twitter: [@Infra_Box](https://twitter.com/Infra_Box) or have look at our Slack channel [infrabox.slack.com](https://infrabox.slack.com/).

|Component|Coverage|
|---------|--------|
|github-review|[![coverage](https://infrabox.ninja/api/v1/projects/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=ib/test/github-review)](https://infrabox.ninja/dashboard/#/project/infrabox)|
|pyinfrabox|[![coverage](https://infrabox.ninja/api/v1/projects/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=ib/test/pyinfrabox)](https://infrabox.ninja/dashboard/#/project/infrabox)|
|registry-auth|[![coverage](https://infrabox.ninja/api/v1/projects/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=ib/test/registry-auth)](https://infrabox.ninja/dashboard/#/project/infrabox)|
