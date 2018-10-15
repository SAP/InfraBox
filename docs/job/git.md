# Job Type: Git
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
|branch|false|string|master|branch to clone initially
|commit|true|string||branch name or commit sha|
|depends_on|false|[Dependency Configuration](/docs/job/dependencies.md)|[]|Jobs may have dependencies. You can list all jobs which should finish before the current job may be executed.|
|environment|false|[Environment Variables](/docs/job/env_vars.md)|{}|Can be used to set environment variables for the job.|
|infrabox_file|false|string|infrabox.json|Path to an `infrabox.json` file in the repo to be used as sub-workflow|
