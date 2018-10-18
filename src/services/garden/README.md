# Gardener Service
The InfraBox Garden Service can be used to dynamically provision a Kubernetes Cluster for an InfraBox job.

## Usage

```json
{
    "version": 1,
    "jobs": [{
        "type": "docker",
        "name": "hello-kubernetes",
        "build_only": false,
        "docker_file": "infrabox/hello-kubernetes/Dockerfile",
        "resources": {
            "limits": { "cpu": 1, "memory": 1024 }
        },
        "services": [{
            "apiVersion": "garden.service.infrabox.net/v1alpha1",
            "kind": "ShootCluster",
            "metadata": {
                "name": "my-cluster"
            },
            "spec": {
                "diskSize": 100,
                "machineType": "m4.xlarge",
                "enableAutoscaling": false,
                "maxNodes": 1,
                "minNodes": 1,
                "zone": "eu-central-1a",
                "clusterVersion": "1.10",
            }
        }]
    }]
}
```

The Shoot Cluster credentials will be available under `/var/run/infrabox.net/services/<service-name>/` (in the example above the service name is `my-cluster`) as files:

- ca.crt
- client.crt
- client.key
- endpoint
- username
- password

You may configure kubectl in your job as follows:

```bash
#!/bin/bash -e
SERVICE_NAME="my-cluster"

CA_CRT="/var/run/infrabox.net/services/$SERVICE_NAME/ca.crt"
CLIENT_CRT="/var/run/infrabox.net/services/$SERVICE_NAME/client.crt"
CLIENT_KEY="/var/run/infrabox.net/services/$SERVICE_NAME/client.key"

ENDPOINT=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/endpoint)
PASSWORD=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/password)
USERNAME=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/username)

kubectl config set-cluster $SERVICE_NAME \
    --server=$ENDPOINT \
    --certificate-authority=$CA_CRT

kubectl config set-credentials admin \
    --certificate-authority=$CA_CRT \
    --client-certificate=$CLIENT_CRT \
    --client-key=$CLIENT_KEY \
    --username=$USERNAME \
    --password=$PASSWORD

kubectl config set-context default-system \
    --cluster=$SERVICE_NAME \
    --user=admin

kubectl config use-context default-system

kubectl get pods
```

## Install
To install the service in your Kubernetes cluster you have to first create a AWS Service Account and configure gardener to use it (secretBindingRef). Next, create a kubeconfig which this service will use to communicate with Gardener. Create a secret containing the kubeconfig:
```bash
kubectl -n infrabox-system create secret generic infrabox-service-garden-sa --from-file ./garden_kubeconfig
```

The names of the secret and the secretBindingRef can be chosen arbitrarily. The service will read the names from the environment variables mentioned below. The name of the kubeconfig entry within the secret (`garden_kubeconfig`) is mandatory. 

Now use helm to install the GCP Service.

```bash
cd infrabox-service-garden
helm install --namespace infrabox-system -n infrabox-service-garden .
```

### Env variables
The garden-operator depends on several environment variables:

#### mandatory:
* `CRENDENTIALS_SECRET`: Name of the secret containing the kubeconfig for Gardener. Within the secret, the config must be stored under the name `garden_kubecfg`.
* `GARDEN_NAMESPACE` : The namespace within Gardener to create new shoot clusters in.
* `GARDENER_PROJECTNAME`: Name of the gardener project which will contain the generated clusters.
* `SECRET_BINDING_REF`: secretBindingRef as configured in Gardener.

#### optional
* `LOGLVL`: the logging level to use. Valid values are: `debug`, `info`, `warn`, `error`. default: `warn`.
* `AWS_MAINTENANCE_AUTOUPDATE`: boolean. Enables autoupdate of kubernetes. default: `true`.
* `AWS_MAINTENANCE_AUTOUPDATE_TWBEGIN`: Begin of the maintenance window. default: `220000+0100`. If used, must be set in conjunction with `AWS_MAINTENANCE_AUTOUPDATE_TWBEND`.
* `AWS_MAINTENANCE_AUTOUPDATE_TWBEND`: End of the maintenance window. default: `230000+0100`. If used, must be set in conjunction with `AWS_MAINTENANCE_AUTOUPDATE_TWBEGIN`.
  