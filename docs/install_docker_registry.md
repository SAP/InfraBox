# Setup credentials for docker registry
InfraBox pushes jobs to its own docker registry. Please setup admin credentials. You may later use them to push and pull all images from the registry.
Users will only have access to their own projects with their authentication tokens.

Create for namespace infrabox-system AND infrabox-worker.

    kubectl -n <NAMESPACE> create secret generic \
        infrabox-docker-registry \
        --from-literal=username=<USERNAME> \
        --from-literal=password=<PASSWORD>
