# Building InfraBox docker images

To build the images you need meet these requirements:

- Checkout InfraBox code from github
- Docker installed
- infraboxcli installed

To build the images

    cd deployment
    ./build.sh <docker_registry> <image_tag>

You may now pus the images into your docker registry.

    docker push <docker_registry><component>:<image_tag>

See also *docker images* for the exact names of the images.
Remember the image names and tags as you will later need them for the configuration of your InfraBox deployment.
