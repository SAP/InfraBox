# Image Source Registry
If your images have to be pulled from a private registry you may configure the credentials for each job.

## Docker Registry
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
|password|false|[Secret](/docs/job/secrets.md)||Secret containing the password|

## ECR
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
|access\_key\_id|true|[Secret](/docs/job/secrets.md)||Secret containing the AWS `Access Key ID`|
|secret\_access\_key|true|[Secret](/docs/job/secrets.md)||Secret containing AWS `Secret Access Key`|

### GCR
```json
{
    "type": "docker",
    ...
    "registries": [{
        "type": "gcr",
        "host": "eu.gcr.io",
        "repository": "<project-id>/<repo-name>",
        "service_account": { "$secret": "GCP_SERVICE_ACCOUNT" },
    }]
}
```

| Name | Required | Type | Default | Description |
|------|----------|------|---------|-------------|
|type|true|string||Has to be "gcr"|
|host|true|string||GCR endpoint i.e. us.gcr.io|
|repository|true|string||Name of the repository|
|service\_account|true|[Secret](/docs/job/secrets.md)||Secret containing the GCP `Service Account` with role `Storage Admin`|
