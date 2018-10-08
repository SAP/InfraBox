# Repository
With the repository configuration you can define how InfraBox should clone your git repository.

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
