# GCP Service
The InfraBox GCP Service can be used to dynamically provision a Kubernetes Cluster for an InfraBox job.

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
            "apiVersion": "gcp.service.infrabox.net/v1alpha1",
            "kind": "GKECluster",
            "metadata": {
                "name": "my-cluster"
            },
            "spec": {
                "diskSize": 100,
                "machineType": "n1-standard-1",
                "enableNetworkPolicy": false,
                "disableLegacyAuthorization": false,
                "enablePodSecurityPolicy": true,
                "numNodes": 1,
                "preemptible": true,
                "enableAutoscaling": false,
                "maxNodes": 1,
                "minNodes": 1,
                "zone": "us-east1-b"
            }
        }]
    }]
}
```

The GKE Cluster credentials will be available under `/var/run/infrabox.net/services/<service-name>/` (in the example above the service name is `my-cluster`) as files:

- ca.crt
- client.crt (deprecated)
- client.key (deprecated)
- endpoint
- token
- kubeconfig
- username (deprecated)
- password (deprecated)

You may configure kubectl in your job as follows:

```bash
#!/bin/bash -e
SERVICE_NAME="my-cluster"

CA_CRT="/var/run/infrabox.net/services/$SERVICE_NAME/ca.crt"

ENDPOINT=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/endpoint)
TOKEN=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/token)

kubectl config set-cluster $SERVICE_NAME \
    --server=$ENDPOINT \
    --embed-certs=true \
    --certificate-authority=$CA_CRT

kubectl config set-credentials admin \
    --token=$TOKEN

kubectl config set-context default-system \
    --cluster=$SERVICE_NAME \
    --user=admin

kubectl config use-context default-system

kubectl get pods
```

or using

```
export KUBECONFIG="/var/run/infrabox.net/services/$SERVICE_NAME/kubeconfig"
```

## Install
To install the service in your Kubernetes cluster you have to first create a GCP Service Account with `Kubernetes Engine Admin` and `Service Account User` roles.
Download the service account json file and save it as `service_account.json`. Then create a secret for it:

```bash
kubectl -n infrabox-system create secret generic infrabox-service-gcp-sa --from-file ./service_account.json
```

Now use helm to install the GCP Service.

```bash
cd infrabox-service-gcp
helm install --namespace infrabox-system -n infrabox-service-gcp .
```
