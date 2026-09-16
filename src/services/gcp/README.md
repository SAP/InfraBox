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
                "stackType": "ipv4-ipv6",
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

## Spec Reference

| Field | Type | Default | Description |
|---|---|---|---|
| `zone` | string | — | GCP zone (required) |
| `machineType` | string | — | GKE node machine type |
| `numNodes` | int | — | Number of nodes |
| `diskSize` | int | — | Boot disk size in GB |
| `clusterVersion` | string | — | Kubernetes version (e.g. `1.37`) |
| `preemptible` | bool | false | Use preemptible nodes |
| `enableAutoscaling` | bool | false | Enable cluster autoscaling |
| `minNodes` | int | — | Minimum nodes (requires `enableAutoscaling`) |
| `maxNodes` | int | — | Maximum nodes (requires `enableAutoscaling`) |
| `enableNetworkPolicy` | bool | false | Enable Kubernetes network policy |
| `disableLegacyAuthorization` | bool | false | Disable legacy ABAC authorization |
| `enablePodSecurityPolicy` | bool | false | Enable Pod Security Policy |
| `stackType` | string | — | Set to `ipv4-ipv6` for dual-stack networking |
| `enableManagedPrometheus` | bool | false | Enable Google Managed Prometheus |
| `serviceCidr` | string | `/18` | Services IPv4 CIDR |
| `clusterCidr` | string | `/18` | Pods IPv4 CIDR |
| `keepAlive` | bool | false | Keep cluster running after job ends (see below) |

## Long-Running Clusters (keepAlive)

By default, GKE clusters are deleted as soon as the InfraBox job finishes. Set `keepAlive: true` to keep the cluster running after the job ends — useful for debugging or extended testing scenarios.

```json
"services": [{
    "apiVersion": "gcp.service.infrabox.net/v1alpha1",
    "kind": "GKECluster",
    "metadata": {
        "name": "my-cluster"
    },
    "spec": {
        "zone": "us-east1-b",
        "machineType": "n1-standard-1",
        "numNodes": 1,
        "diskSize": 100,
        "clusterVersion": "1.37",
        "keepAlive": true
    }
}]
```

When `keepAlive: true`:
- The cluster is tagged with the GCP label `infrabox-keep-alive=true` at creation time
- InfraBox removes its CRD record when the job ends but does **not** delete the GKE cluster
- The cluster is excluded from InfraBox's GC loop

**Finding keepAlive clusters:**
```bash
gcloud container clusters list \
    --filter="labels.infrabox-keep-alive=true" \
    --format="table(name,zone,status,createTime)"
```

**Deleting a keepAlive cluster:**
```bash
gcloud container clusters delete <name> --zone <zone>
```

> **Note:** keepAlive clusters are not managed by InfraBox after the job ends. You are responsible for deleting them to avoid ongoing GCP costs.

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
