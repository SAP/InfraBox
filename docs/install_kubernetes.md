# Install InfraBox on Kubernetes
These instructions are meant to be used for a Kubernetes cluster which runs in you local environment.

## Requirements
- Kubernetes 1.7
    - RBAC should be enabled
- helm has to be installed
    - See [here](https://gist.github.com/mgoodness/bd887830cd5d483446cc4cd3cb7db09d) for how to configure helm with rbac
- kubectl must be installed locally
    - kubectl must be configured to point to your Kubernetes cluster

## Generate docker images
See [Building InfraBox Docker Images](docs/build_images.md).

## Installation
InfraBox ships with an installation script in deploy/install.py. You can use it to generate the configuration and helm charts for Kubernetes. The following sections describes which options you should pass to install.py for a propper installation.

Set the output directory in which the helm charts will be stored.

    -o /tmp/infrabox

This will later contain all the configuration files including password and other secrets. So you may want to store it at a safe place. You can also use it to upgrade InfraBox in case you changed the configuration.

For a Kubernetes installation use:

    --platform Kubernetes

## Configure InfraBox installation

1. [Docker Registry](docs/configure/docker_registry.md)
2. [PostgreSQL](docs/configure/postgres.md)
3. [Storage](docs/configure/s3.md)

Optionally you may want to configure:

4. [Gerrit](docs/configure/gerrit.md)
5. [GitHub](docs/configure/github.md)
6. [LDAP](docs/configure/ldap.md)
7. [TLS](docs/configure/tls.md)

## Configure URLs
InfraBox internally needs to know under which URL the different services will be reachable at the end. Without this information some generated links would not work and InfraBox would not be able to push to its internal registry.

Every service is assigned a port which is routed on each Kubernetes node to the service. So you can use one IP address of your Kubernetes worker nodes (or master) and the corresponding port of the service. i.e.:

    --use-k8s-nodeports
    --api-url http://<K8S_MASTER_IP>:30200
    --dashboard-url http://<K8S_MASTER_IP>:30201
    --docs-url http://<K8S_MASTER_IP>:30202
    --docker-registry-url http://<K8S_MASTER_IP>:30203

The ports are configurable with (these are the default values):

    --api-k8s-nodeport 30200
    --dashboard-k8s-nodeport 30201
    --docs-k8s-nodeport 30202
    --docker-registry-k8s-nodeport 30203

## Finally
Now you should have the most important things configured. Run install.py with all these options and cd into the output directory.

If you did not setup TLS for the docker-registry you may have to change InfraBox' docker daemon configuration to allow the internal registry to be insecure.
For this change config/docker/daemon.json to

    {
        "insecure-registries": ["<K8S_MASTER_IP:30203"]
    }

If you have other registries in your network which are not secure you may also add them.


Now the last step is to run install.sh. It will deploy all the necessary components to your Kubernetes cluster.

# Update InfraBox
If you want to update your InfraBox installation you can use the generated update.sh.

# Uninstall InfraBox
If you want to uninstall your InfraBox on Kubernetes run:

    helm delete --purge infrabox

This will not delete data stored in S3 or your database. You have to manually delete these things.
