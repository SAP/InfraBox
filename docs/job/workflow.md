# Job Type: Workflow
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
|depends_on|false|[Dependency Configuration](/docs/job/dependencies.md)|[]|Jobs may have dependencies. You can list all jobs which should finish before the current job may be executed.|
