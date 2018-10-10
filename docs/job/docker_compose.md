# Job Type: Docker-Compose
Sometimes you want to start multiple containers to test your application. For this InfraBox supports also docker-compose. You can specify a docker-compose.yml and InfraBox will start it as one job.

```json
{
    "version": 1,
    "jobs": [{
        "type": "docker-compose",
        "name": "test",
        "docker_compose_file": "infrabox/test/docker-compose.yml",
        "resources": { "limits": { "cpu": 1, "memory": 1024 } },
        "cache": { ... },
        "timeout": 3600,
        "depends_on": ["other_job_name"],
        "environment": { ... }
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "docker-compose" to run multiple containers|
|name|true|string||Name of the job|
|docker_compose_file|true|string||Path to the `docker-compose.yml`|
|resources|true|[Resource Configuration](/docs/job/resources.md)||Specify the required resources for your job|
|cache|false|[Cache Configuration](/docs/job/cache.md)|{}|Configure the caching behavior|
|timeout|false|integer|3600|Timeout in seconds after which the job should be killed. Timeout starts when the job is set to running|
|depends_on|false|[Dependency Configuration](/docs/job/dependencies.md)|[]|Jobs may have dependencies. You can list all jobs which should finish before the current job may be executed.|
|environment|false|[Environment Variables](/docs/job/env_vars.md)|{}|Can be used to set environment variables for the job.|
