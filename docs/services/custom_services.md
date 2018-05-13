# Implement an InfraBox Service
InfraBox supports an extension mechanism called Services. A Service is a way of providing additional resources or other services to a job. See our example on how to use the GCP Service to create a Kubernetes cluster for a job.

InfraBox services have to be build as Kubernetes controllers (aka Operator). A little bit of backgroud information about what controllers are and how they can be implemented:

- [Kubernetes Sample Controller](https://github.com/kubernetes/sample-controller)
- [CoreOS Operators](https://coreos.com/operators/)

Services can be used in your job definition:

```
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
            "apiVersion": "my-custom-service/v1alpha1",
            "kind": "MyCustomKind",
            "metadata": {
                "name": "my-cluster"
            },
            "spec": {
                "some": "value",
            }
        }]
    }]
}
```

Before the job is supposed to be started InfraBox will take the service definition, rewrite it and send it to the Kubernetes API Server:

```
{
    "apiVersion": "my-custom-service/v1alpha1",
    "kind": "MyCustomKind",
    "metadata": {
        "name": "<UNIQUE_NAME>",
        "namespace": "<SOME_NAMESPACE>"
        "labels": {
            "service.infrabox.net/secret-name": "<SECRET_NAME>"
        }
    },
    "spec": {
        "some": "value",
    }
}
```

If you want to create a custom Service all you have to do is to create a Kubernetes controller and a corresponding CRD. The CRD can be used in the service definition of the job.
The controller has to follow a few conventions to work properly with InfraBox.

Every controller has to create a secret with the value of the label `service.infrabox.net/secret-name` as name in the specified namespace of the service. The content of the secret will be mounted in the job to `/var/run/infrabox.net/services/<SERVICE_NAME>` (the service name specified in the job, not the one overwritten by InfraBox. So in the example above "my-cluster" will be the Service name).

The Controller has to set two status fields:
- _status.status_: Can be either
    - `pending`: while resource is being created
    - `ready`: when resource is ready to use, InfraBox will start the job if all services are ready
    - `error`: if an error occurd, the InfraBox job will end with `error`
- _status.message_: The message will be reported to the InfraBox job if your service status is set to `error`

If you have implemented such a controller just create the CRD in the kubernetes cluster and deploy your controller. Now you can use it as a Service to provide additional resources to your job.
