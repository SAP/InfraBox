# Cache Configuration
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


