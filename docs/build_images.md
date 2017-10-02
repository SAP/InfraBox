## Build Containers
To build the containers you need to have installed:

- [infraboxcli](https://github.com/infrabox/cli)
- [docker](https://www.docker.com/)

To run InfraBox you first have to build all its docker containers. To do so run from the root directory of the project:

    ./deploy/build.sh <YOUR_DOCKER_REGISTRY>

i.e.:

    ./deploy/build.sh 192.168.157.129:5000/

Now you have all the containers build. If you want to push the images to your docker registry you may use

    ./deploy/push.sh <YOUR_DOCKER_REGISTRY>
