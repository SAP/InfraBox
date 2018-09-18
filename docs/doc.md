# Job Configuration
If you want to run jobs on InfraBox you have to create a file called `infrabox.json` in the root directory of your project. It tells InfraBox what jobs are part of the project and which dependencies between the jobs exist. The basic structure of the file is as follows:

```json
{
    "version": 1,
    "jobs": [
        ...
    ]
}
```

| Name | Required | Type | Description |
|------|----------|------|-------------|
|version|true|number|Currently only valid value is 1.|
|jobs|true|array of job definitions|A list of the actual jobs to run. It can be either<ul><li>[docker](#job-docker)</li><li>[docker-compose](#job-docker-compose)</li><li>[git](#job-git)</li><li>[workflow](#job-workflow)</li></ul>|

## Job: Docker
The job type docker is one of the most important jobs. You can use it to run any Docker container you like.

```json
{
    "version": 1,
    "jobs": [{
        "type": "docker",
        "name": "build",
        "docker_file": "infrabox/build-and-test/Dockerfile",
        "command": ["echo", "hello world"]
        "resources": { "limits": { "cpu": 1, "memory": 1024 } },
        "build_only": false,
        "build_context": "...",
        "cache": { ... },
        "timeout": 3600,
        "depends_on": ["other_job_name"],
        "environment": { ... },
        "build_arguments": { ... },
        "deployments": [ ... ],
        "security_context": { ... },
        "repository": { ... },
        "registries": []
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "docker" to run a single Docker container|
|name|true|string||Name of the job|
|docker_file|true|string||Path to the `Dockerfile`|
|command|false|string||The command in [exec form](https://docs.docker.com/engine/reference/builder/#cmd) to be used when the container is run. Ignored if `build_only=false`|
|resources|true|[Resource Configuration](#resource-configuration)||Specify the required resources for your job|
|build_only|true|boolean|true|If set to true the container will only be build but not run. Use it if you only want to build a container and push it to a registry. See here for how to push to a docker registry.|
|build_context|false|string||Specify the docker build context. If not set the directory containing the `infrabox.json` file will be used.|
|cache|false|[Cache Configuration](#cache-configuration)|{}|Configure the caching behavior|
|timeout|false|integer|3600|Timeout in seconds after which the job should be killed. Timeout starts when the job is set to running|
|depends_on|false|[Dependency Configuration](#dependency-configuration)|[]|Jobs may have dependencies. You can list all jobs which should finish before the current job may be executed.|
|environment|false|object|{}|Can be used to set environment variables for the job. See Environment Variables for more details.|
|build_arguments|false|object|{}|Can be used to set docker build arguments. See Build Arguments for more details.|
|deployments|false|[Deployment Configuration](#deployments)|[]|Push your images to a registry|
|security_context|false|[Security Context](#security-context)|[]|Configure security related options|
|repository|false|[Repository Configuration](#repository)|{}|Configure git repository options|
|registries|false|[Source Registry Configuration](#image-source-registry)|[]|Configure the source registries|

### Deployments
The docker images which have been build can also be pushed to a docker registry by InfraBox.

### Docker Registry
You would add a deployment to your job:

```json
{
    "type": "docker",
    ...
    "deployments": [{
        "type": "docker-registry",
        "host": "<my_registry>:5000",
        "repository": "repo-name",
        "tag": "some optional tag",
        "target": "target build stage",
        "username": "your_username",
        "password": { "$secret": "SECRET_NAME_FOR_YOUR_PASSWORD" }
    }]
}
```

Deployments are currently only supported for `docker` job types.

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "docker-registry"|
|host|true|string||Host of the registry. I.e. my-registry.com:5000|
|repository|true|string||Name of the repository|
|tag|false|string|build\_\<NUMBER>|The tag of the image|
|target|false|string||When building a Dockerfile with multiple build stages `target` can be used to specify an intermediate build stage by name as a final stage for the resulting image which should be deployed|
|username|false|string||Username to be used with the registry|
|password|false|[Secret](#secrets)||Secret containing the password|

### ECR
You would add a deployment to your job:

```json
{
    "type": "docker",
    ...
    "deployments": [{
        "type": "ecr",
        "host": "<my_registry>",
        "repository": "repo-name",
        "tag": "some optional tag",
        "target": "target build stage",
        "region": "region",
        "access_key_id": { "$secret": "SECRET_KEY_ID" },
        "secret_access_key": { "$secret": "SECRET_ACCESS_KEY" }
    }]
}
```

Deployments are currently only supported for `docker` job types.

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "ecr"|
|host|true|string||ECR endpoint|
|repository|true|string||Name of the repository|
|tag|false|string|build\_\<NUMBER>|The tag of the image|
|target|false|string||When building a Dockerfile with multiple build stages `target` can be used to specify an intermediate build stage by name as a final stage for the resulting image which should be deployed|
|region|true|string||AWS Region|
|access\_key\_id|true|[Secret](#secrets)||Secret containing the AWS `Access Key ID`|
|secret\_access\_key|true|[Secret](#secrets)||Secret containing AWS `Secret Access Key`|

### GCR
You would add a deployment to your job:

```json
{
    "type": "docker",
    ...
    "deployments": [{
        "type": "gcr",
        "host": "eu.gcr.io",
        "repository": "<project-name>/<repo-name>",
        "tag": "some optional tag",
        "target": "target build stage",
        "service_account": { "$secret": "GCP_SERVICE_ACCOUNT" },
    }]
}
```

Deployments are currently only supported for `docker` job types.

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "gcr"|
|host|true|string||GCR endpoint i.e. us.gcr.io|
|repository|true|string||Name of the repository|
|tag|false|string|build\_\<NUMBER>|The tag of the image|
|target|false|string||When building a Dockerfile with multiple build stages `target` can be used to specify an intermediate build stage by name as a final stage for the resulting image which should be deployed|
|region|true|string||AWS Region|
|service\_account|true|[Secret](#secrets)||Secret containing the GCP `Service Account` with role `Storage Admin`|


### Build Arguments
To set docker build arguments create an object with the names and values for `build_arguments`.

```json
{
    "version": 1,
    "jobs": [{
        "type": "docker",
        ...
        "build_arguments": {
            "ARG_1": "My value",
            "ANOTHER_ARG": "some other value
        }
    }]
}
```

Build arguments are only supported for `docker` job types.

### Repository

```json
{
    "version": 1,
    "jobs": [{
        "type": "docker",
        ...
        "repository": {
            "clone": true,
            "full_history": false,
            "submodules": true
        }
    }]
}

```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|clone|false|boolean|true|Set to `false` if the git repository should not be cloned|
|full_history|false|boolean|false|By default InfraBox does not fetch the full git history to speed up builds. If you need the full history set it to `true`|
|submodules|false|boolean|true|Set to `true` if submodules should be cloned|

## Job: Docker Image
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
|type|true|string||Has to be "docker" to run a single Docker container|
|name|true|string||Name of the job|
|image|true|string||Image to use, i.e. `alpine:latest`|
|command|true|string||The command in [exec form](https://docs.docker.com/engine/reference/builder/#cmd)|
|resources|true|[Resource Configuration](#resource-configuration)||Specify the required resources for your job|
|build_context|false|string||Specify the docker build context. If not set the directory containing the `infrabox.json` file will be used.|
|cache|false|[Cache Configuration](#cache-configuration)|{}|Configure the caching behavior|
|timeout|false|integer|3600|Timeout in seconds after which the job should be killed. Timeout starts when the job is set to running|
|depends_on|false|[Dependency Configuration](#dependency-configuration)|[]|Jobs may have dependencies. You can list all jobs which should finish before the current job may be executed.|
|environment|false|object|{}|Can be used to set environment variables for the job. See Environment Variables for more details.|
|deployments|false|[Deployment Configuration](#deployments)|[]|Push your images to a registry|
|security_context|false|[Security Context](#security_context)|[]|Configure security related options|
|repository|false|[Repository Configuration](#repository)|{}|Configure git repository options|
|registries|false|[Source Registry Configuration](#image-source-registry)|[]|Configure the source registries|
|run|false|boolean|true|Set to false if you have a deployment configured and only want to push an image but not execute it|

### Image Source Registry
If your images have to be pulled from a private registry you may configure the credentials for each job.

#### Docker Registry
```json
{
    "type": "docker",
    ...
    "registries": [{
        "type": "docker-registry",
        "host": "<my_registry>:5000",
        "repository": "repo-name",
        "username": "your_username",
        "password": { "$secret": "SECRET_NAME_FOR_YOUR_PASSWORD" }
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "docker-registry"|
|host|true|string||Host of the registry. I.e. my-registry.com:5000|
|repository|true|string||Name of the repository|
|username|false|string||Username to be used with the registry|
|password|false|[Secret](#secrets)||Secret containing the password|

#### ECR
```json
{
    "type": "docker",
    ...
    "registries": [{
        "type": "ecr",
        "host": "<my_registry>",
        "repository": "repo-name",
        "region": "region",
        "access_key_id": { "$secret": "SECRET_KEY_ID" },
        "secret_access_key": { "$secret": "SECRET_ACCESS_KEY" }
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "ecr"|
|host|true|string||ECR endpoint|
|repository|true|string||Name of the repository|
|region|true|string||AWS Region|
|access\_key\_id|true|[Secret](#secrets)||Secret containing the AWS `Access Key ID`|
|secret\_access\_key|true|[Secret](#secrets)||Secret containing AWS `Secret Access Key`|

## Job: Docker-Compose
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
|resources|true|[Resource Configuration](#resource-configuration)||Specify the required resources for your job|
|cache|false|[Cache Configuration](#cache-configuration)|{}|Configure the caching behavior|
|timeout|false|integer|3600|Timeout in seconds after which the job should be killed. Timeout starts when the job is set to running|
|depends_on|false|array of job names|[]|Jobs may have dependencies. You can list all jobs which should finish before the current job may be executed.|
|environment|false|object|{}|Can be used to set environment variables for the job. See Environment Variables for more details.|

## Job: Git
It's not necessary to have all your job definitions in your own project. With the git job type you can include job definitions for any accessible git repository.

An example git job definition:
```json
{
    "version": 1,
    "jobs": [{
        "type": "git",
        "name": "some-external-jobs",
        "clone_url": "https://github.com/SAP/infrabox-examples.git",
        "commit": "master",
        "depends_on": [ ... ],
        "environment": { ... },
        "infrabox_file": "infrabox.json"
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "git" to include a workflow from a repository|
|name|true|string||Name of the job|
|clone_url|true|string||Url to clone the git repository|
|commit|true|string||branch name or commit sha|
|depends_on|false|array of job names|[]|Jobs may have dependencies. You can list all jobs which should finish before the current job may be executed.|
|environment|false|object|{}|Can be used to set environment variables for the job. See Environment Variables for more details.|
|infrabox_file|false|string|infrabox.json|Path to an `infrabox.json` file in the repo to be used as sub-workflow|

## Job: Workflow
If you have many jobs you might want to structure them in different files.

An example job definition:

```json
{
    "version": 1,
    "jobs": [{
        "type": "workflow",
        "name": "deploy",
        "infrabox_file": "deployments.json",
        "depends_on": ["test"]
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "git" to include a workflow from the same repository|
|name|true|string||Name of the job|
|infrabox_file|true|string||Path to another `infrabox.json` file|
|depends_on|false|array of job names|[]|Jobs may have dependencies. You can list all jobs which should finish before the current job may be executed.|

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

## Cache Configuration
InfraBox can cache custom data and images for you. This can significantly speed up your jobs. You can control the caching behavior with

```json
{
    "version": 1,
    "jobs": [{
        ...
        "cache": {
            "data": true,
            "image": false
        }
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|data|false|boolean|`true`|If set to false the content of /infrabox/cache will not be restored|
|image|false|boolean|`false`|If set to true the images of each job will be cached in an internal registry.|

Sometimes it's useful to keep some data from one run of a container to the next one. Maybe you have a nodejs project and don't want to install your dependencies every time. For such uses cases InfraBox mounts the directory `/infrabox/cache` into every container. Everything which you store in this directory will be available at the same place in the next run. So for your nodejs project you could simply copy your node_modules directory in there.

## Environment Variables
You can set environment variables in your job definition. They will be available during the run phase of the container, not during build.

```json
{
    "version": 1,
    "jobs": [{
        ...
        "environment": {
            "SOME_ENV_VAR": "My value",
            "ANOTHER_ENV_VAR": "Another value"
        }
    }]
}
```

### Using secrets as environment variable

If you have created a [secret](#secrets) you can make it available as a environment variable.

```json
{
    "version": 1,
    "jobs": [{
        ...
        "environment": {
            "SOME_SECRET_VALUE": { "$secret": "NAME_OF_THE_SECRET" },
        }
    }]
}
```

## Resource Configuration

### Job resource limits
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

## Dependency Configuration
To model dependencies between jobs you simply use `depends_on` in the job definition. As an example we create tree jobs `A`, `B` and `C`. `C` depends on `A` and `B`.

```json
{
    "version": 1,
    "jobs": [{
        "name": "A",
        ...
    }, {
        "name": "B",
        ...
    }, {
        "name": "C",
        ...
        "depends_on": ["A", "B"]
    }]
}
```
Jobs `A` and `B` would start in parallel and `C` would only start if `A` and `B` succeeded successfully. If either of the parent jobs failed `C` would not be started at all. You may use dependencies with all available job types.

It's also possible to specify the required job state of the parent. So if you want to run the child job only if the parent has failed you can do:

```json
{
    "version": 1,
    "jobs": [{
        "name": "A",
        ...
    }, {
        "name": "B",
        ...
        "depends_on": [{"job": "A", "on": ["failure"]}]
    }]
}
```

Possible values for `on` are:
- `failure`
- `finished`
- `error`
- `*`  results in all -> `failed`, `finished`, `error`

So if you have a cleanup job which you want to run allways, independent of the parent state, use `*`.

### Transfer data between jobs

If you have defined dependencies between your jobs you can also transfer data between them. The parent job may produce some output which the child job may access.

Every InfraBox job has automatically an output folder mounted under `/infrabox/output`. All data which is written into this directory will be accessible by the direct child jobs. The data is made accessible in the child in the `/infrabox/inputs/<parent_job_name>` directory.

Suppose we have the following job definition:

```json
{
    "version": 1,
    "jobs": [{
        "name": "parent",
        ...
    }, {
        "name": "child",
        ...
        "depends_on": ["parent"]
    }]
}
```

If the the parent job would create the file `/infrabox/output/hello_world.txt` then the child job would be able to access it under `/infrabox/inputs/parent/hello_world.txt`.

# Badges
With InfraBox you can easily create one or mutiple badges like   or   with your custom information. To create a badge simply create a json file like this:

```json
{
    "version": 1,
    "subject": "build",
    "status": "failed",
    "color": "red"
}
```

and save it to `/infrabox/upload/badge/badge.json`. You can also save multiple files with different names in this directory. For every file a separate badge will be created.

# Upload Test Result
InfraBox can show your testresult on a tab at the job detail view. This gives you the possibility to quickly check the results and if one of your tests has failed you can even see the error message and stacktrace if available. To use this feature you only have to copy your testresult file to `/infrabox/upload/testresult`. We will try to auto detect the format of your file. Currently supported file formats are:

- xunit (xml)

# Upload Coverage Result
InfraBox can show your coverage results on a tab at the job detail view. To use this feature you only have to copy your coverage file to `/infrabox/upload/coverage`. We will try to auto detect the format of your file. Currently supported file formats are:

- covertura (xml)
- clover (xml)

# Dynamic Workflows
Often a pre-defined static workflow is not sufficient to handle all use cases. For this InfraBox supports dynamic workflows. Every job in your workflow may produce an `infrabox.json` in its output directory `/infrabox/output/infrabox.json`. All jobs defined in there will be automatically added as predecessor jobs. This give you the options to extend your workflow at runtime.

This feature is extremely useful for bigger projects. Maybe you don't want to run certain tests on a branch or you want to additionaly deploy your containers to an registry if you create a tag.

# Secrets
InfraBox can store secret values for you, so you don't have to store passwords or other secret values in your repository. Login to the InfraBox Dashboard, select your project and go to the Settings tab. There you can create a secret with a name and value. You can use the secrets as:

- [Environment Variable](#environment-variables)
- [Docker Registry Password](#docker-registry)

# Archive
Sometimes it's helpful to store some files for later access. Every file you write to `/infrabox/upload/archive` will later be accessible in the Dashboard for the job.

