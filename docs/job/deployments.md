# Deployments
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
        "always_push": "true or false",
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
|always_push|false|bool|false|Always deploy image, even if container run failed.|
|username|false|string||Username to be used with the registry|
|password|false|[Secret](/docs/job/secrets.md)||Secret containing the password|

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
|access\_key\_id|true|[Secret](/docs/job/secrets.md)||Secret containing the AWS `Access Key ID`|
|secret\_access\_key|true|[Secret](/docs/job/secrets.md)||Secret containing AWS `Secret Access Key`|

### GCR
You would add a deployment to your job:

```json
{
    "type": "docker",
    ...
    "deployments": [{
        "type": "gcr",
        "host": "eu.gcr.io",
        "repository": "<project-id>/<repo-name>",
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
|service\_account|true|[Secret](/docs/job/secrets.md)||Secret containing the GCP `Service Account` with role `Storage Admin`|
