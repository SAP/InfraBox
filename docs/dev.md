# Developer Guide

## Build Images
To build the containers you need to have installed:

- [infraboxcli](https://github.com/infrabox/cli)
- [docker](https://www.docker.com/)

InfraBox uses _infraboxcli_ to build its images. To build all images run from the root directory of the project:

```
    $ ./deploy/build.sh <YOUR_DOCKER_REGISTRY: i.e. localhost:5000>
```

After the images have been build successfully you can either push them to regular registry

```
    $ ./deploy/push.sh <YOUR_DOCKER_REGISTRY>
```

or to google's container registry:

```
    $ ./deploy/push_gcr.sh <YOUR_DOCKER_REGISTRY>
```
