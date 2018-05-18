# Namespace Service
The InfraBox Namespace Service can be used to dynamically provision a Kubernetes namespace in the same cluster the job is running in.

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
            "apiVersion": "namespace.service.infrabox.net/v1alpha1",
            "kind": "ClusterNamespace",
            "metadata": {
                "name": "my-namespace"
            }
        }]
    }]
}
```

The GKE Cluster credentials will be available under `/var/run/infrabox.net/services/<service-name>/` (in the example above the service name is `my-namespace`) as files:

- ca.crt
- endpoint
- token
- namespace

You may configure kubectl in your job as follows:

```bash
#!/bin/bash -e
SERVICE_NAME="my-namespace"

CA_CRT="/var/run/infrabox.net/services/$SERVICE_NAME/ca.crt"

ENDPOINT=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/endpoint)
NAMESPACE=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/namespace)
TOKEN=$(cat /var/run/infrabox.net/services/$SERVICE_NAME/token)

kubectl config set-cluster $SERVICE_NAME \
    --server=$ENDPOINT \
    --certificate-authority=$CA_CRT

kubectl config set-credentials admin \
    --certificate-authority=$CA_CRT \
    --token=$TOKEN

kubectl config set-context default-system \
    --cluster=$SERVICE_NAME \
    --user=admin

kubectl config use-context default-system

# Install helm
helm init --tiller-namespace $NAMESPACE

# wait for tiller to be ready
sleep 20

helm --tiller-namespace $NAMESPACE --namespace $NAMESPACE install --wait --set persistence.enabled=false stable/postgresql

helm --tiller-namespace $NAMESPACE --namespace $NAMESPACE ls
```

## Install
```bash
cd infrabox-service-namespace
helm install --namespace infrabox-system -n infrabox-service-namespace .
```
