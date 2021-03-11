# Job Type: Docker Image
You can also specify an already build image and run it as a job.

```json
{
    "version": 1,
    "jobs": [{
        "type": "docker-image",
        "name": "test",
        "image": "alpine:latest",
        "command": ["echo", "hello world"]
        "resources": { "limits": { "cpu": 1, "memory": 1024 } },
        "build_context": "...",
        "cache": { ... },
        "timeout": 3600,
        "depends_on": ["other_job_name"],
        "deployments": [ ... ],
        "environment": { ... },
        "security_context": { ... },
        "repository": { ... },
        "registries": [],
        "run": true
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "docker-image" to run a single Docker container|
|name|true|string||Name of the job|
|image|true|string||Image to use, i.e. `alpine:latest`|
|command|false|string||The command in [exec form](https://docs.docker.com/engine/reference/builder/#cmd)|
|resources|true|[Resource Configuration](/docs/job/resources.md)||Specify the required resources for your job|
|build_context|false|string||Specify the docker build context. If not set the directory containing the `infrabox.json` file will be used.|
|cache|false|[Cache Configuration](/docs/job/cache.md)|{}|Configure the caching behavior|
|timeout|false|integer|3600|Timeout in seconds after which the job should be killed. Timeout starts when the job is set to running|
|depends_on|false|[Dependency Configuration](/docs/job/dependencies.md)|[]|Jobs may have dependencies. You can list all jobs which should finish before the current job may be executed.|
|environment|false|[Environment Variables](/docs/job/env_vars.md)|{}|Can be used to set environment variables for the job.|
|deployments|false|[Deployment Configuration](/docs/job/deployments.md)|[]|Push your images to a registry|
|security_context|false|[Security Context](/docs/job/security.md)|[]|Configure security related options|
|repository|false|[Repository Configuration](/docs/job/repository.md)|{}|Configure git repository options|
|registries|false|[Source Registry Configuration](/docs/job/source_registry.md)|[]|Configure the source registries|
|run|false|boolean|true|Set to false if you have a deployment configured and only want to push an image but not execute it|
