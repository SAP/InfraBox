# AKS Service
The InfraBox AKS Service can be used to dynamically provision a Kubernetes Cluster for an InfraBox job.

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
            "apiVersion": "azure.service.infrabox.net/v1alpha1",
            "kind": "AKSCluster",
            "metadata": {
                "name": "my-cluster"
            },
            "spec": {
                "diskSize": 100,
                "machineType": "Standard_DS2_v2",
                "numNodes": 3,
                "zone": "westeurope"
            }
        }]
    }]
}
```

The AKS Cluster credentials will be available under `/var/run/infrabox.net/services/<service-name>/` (in the example above the service name is `my-cluster`) as files:

- admin.conf

You may configure kubectl in your job as follows:

```bash
#!/bin/bash -e
SERVICE_NAME="my-cluster"

export KUBECONFIG="/var/run/infrabox.net/services/$SERVICE_NAME/admin.conf"

kubectl get nodes
```

## Install
To install the service in your Kubernetes cluster you have to first create a Azure service principal and then add credentials to infrabox-service-aks/values.yaml:

Now use helm to install the AKS Service.

```bash
cd infrabox-service-aks
helm install --namespace infrabox-system -n infrabox-service-aks .
```
