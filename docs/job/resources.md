# Resource Configuration

Every job on InfraBox requires resource limits. So it can gurantee the resources to each job.

```json
{
    "version": 1,
    "jobs": [{
        ...
        "resources": {
            "limits": {
                "cpu": 0.5,
                "memory": 1024
            },
        }
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|cpu|true|float||Specify the number of CPUs to be used for the job|
|memory|true|integer||Specify the number of MiB of RAM to be used for the job. Value must be an integer and at least 128|
