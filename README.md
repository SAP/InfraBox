# <img src="src\dashboard-client\static\logo_compact_transparent.png" width="200">
[![Build Status](https://infraboxci.datahub.sapcloud.io/api/v1/projects/deb14c11-dcbe-41f0-ade8-9d26e87266c3/state.svg?branch=master)](https://infraboxci.datahub.sapcloud.io/dashboard/#/project/sap-infrabox)
[![REUSE status](https://api.reuse.software/badge/github.com/SAP/InfraBox)](https://api.reuse.software/info/github.com/SAP/InfraBox)


InfraBox is a continuous integration system. It's well suited for cloud native applications and has [native support for kubernetes](https://github.com/SAP/infrabox-examples/tree/master/kubernetes). Watch our short introduction video:

[![Introduction to InfraBox](https://img.youtube.com/vi/O8N2U7d404I/0.jpg)](https://www.youtube.com/watch?v=O8N2U7d404I)

Some of InfraBox's features are:

- [Static and dynamic workflows](https://github.com/SAP/infrabox-examples)
- [Set resource limits (CPU and memory) for each task](https://github.com/SAP/infrabox-examples)
- [GitHub integration](docs/install/configure/github.md)
- [Gerrit integration](docs/install/configure/gerrit.md)
- [LDAP support](docs/install/configure/ldap.md)
- [Periodically schedule builds](docs/cronjobs.md)
- [and many more, see our examples](https://github.com/SAP/infrabox-examples)


## Documentation
All our documentation can be found [here](docs/README.md). You can also look at our [example repository](https://github.com/SAP/infrabox-examples) on how to make use of the different features InfraBox provides.

## How to obtain support
If you need help please post your questions to [Stack Overflow](https://stackoverflow.com/questions/tagged/infrabox).
In case you found a bug please open a [Github Issue](https://github.com/SAP/infrabox/issues).

## Roadmap

### 1.2
- Bugfixes
- Improve Documentation (installation, job definition & API)
- Add support for SAML
- Quota management on user and project level

### 1.x
- [knative](https://cloud.google.com/knative/) integration
- Service for creating EKS K8s Clusters
- More to come, _your idea here_

## Contribute
Any contribution is highly appreciated. See our [developer's documentation](docs/dev.md) for details.

## License
Copyright (c) 2018 SAP SE or an SAP affiliate company. All rights reserved.
This file is licensed under the Apache Software License, v. 2 except as noted otherwise in the [LICENSE file](LICENSE).
