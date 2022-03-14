# Job Type: Docker
The job type docker is one of the most important jobs. You can use it to run any Docker container you like.

```json
{
    "version": 1,
    "jobs": [{
        "type": "docker",
        "name": "build",
        "docker_file": "infrabox/build-and-test/Dockerfile",
        "command": ["echo", "hello world"],
        "resources": { "limits": { "cpu": 1, "memory": 1024 } },
        "build_only": false,
        "enable_docker_build_kit": true,
        "build_context": "...",
        "cache": { ... },
        "timeout": 3600,
        "depends_on": ["other_job_name"],
        "environment": { ... },
        "build_arguments": { ... },
        "deployments": [ ... ],
        "security_context": { ... },
        "repository": { ... },
        "registries": [],
        "target": "specificstage"
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "docker" to run a single Docker container|
|name|true|string||Name of the job|
|docker_file|true|string||Path to the `Dockerfile`|
|command|false|string||The command in [exec form](https://docs.docker.com/engine/reference/builder/#cmd) to be used when the container is run. Ignored if `build_only=true`|
|resources|true|[Resource Configuration](/docs/job/resources.md)||Specify the required resources for your job.|
|build_only|true|boolean|true|If set to true the container will only be build but not run. Use it if you only want to build a container and push it to a registry. See here for how to push to a docker registry.|
|enable_docker_build_kit|false|boolean|false|If set to true, InfraBox will try to use the Dokcer Buildkit to build the containers. For more details, please refer to [Docker docs](https://docs.docker.com/develop/develop-images/build_enhancements/)|
|build_context|false|string||Specify the docker build context. If not set the directory containing the `infrabox.json` file will be used.|
|cache|false|[Cache Configuration](/docs/job/cache.md)|{}|Configure the caching behavior|
|timeout|false|integer|3600|Timeout in seconds after which the job should be killed. Timeout starts when the job is set to running|
|depends_on|false|[Dependency Configuration](/docs/job/dependencies.md)|[]|Jobs may have dependencies. You can list all jobs which should finish before the current job may be executed.|
|environment|false|[Environment Variables](/docs/job/env_vars.md)|{}|Can be used to set environment variables for the job.|
|build_arguments|false|[Build Arguments](#build-arguments)|{}|Can be used to set docker build arguments. |
|deployments|false|[Deployment Configuration](/docs/job/deployments.md)|[]|Push your images to a registry.|
|security_context|false|[Security Context](#security-context)|[]|Configure security related options,|
|repository|false|[Repository Configuration](/docs/job/repository.md)|{}|Configure git repository options.|
|registries|false|[Source Registry Configuration](/docs/job/source_registry.md)|[]|Configure the source registries.|
|target|false|string||Stop at a specific build stage when using a multi-stage Dockerfile. [Reference](https://docs.docker.com/develop/develop-images/multistage-build/#stop-at-a-specific-build-stage).|

## Build Arguments
To set docker build arguments create an object with the names and values for `build_arguments`.

```json
{
    "version": 1,
    "jobs": [{
        "type": "docker",
        ...
        "build_arguments": {
            "ARG_1": "My value",
            "ANOTHER_ARG": "some other value"
        }
    }]
}
```

Build arguments are only supported for `docker` job types.

## Security Context

```json
{
    "version": 1,
    "jobs": [{
        ...
        "security_context": {
            "privileged": false
        }
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|privileged|false|boolean|false|If set to true the container will be run in privileged mode|
