## Configure Docker Registry
Set the docker registry in which the InfraBox images have been pushed

    --docker-registry <YOUR_DOCKER_REGISTRY>

InfraBox starts its own docker registry to store the images of the jobs. You have to set a admin username and password for this registry. Images can only be pushed to this registry with the provided username and password.

    --docker-registry-admin-username <CHOSE_A_USERNAME>
    --docker-registry-admin-password <CHOSE_A_PASSWORD>

TODO: insecure registry
