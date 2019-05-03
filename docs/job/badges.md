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

Querying badges can be done using badge.svg endpoint independended of the original filename:

```
<infrabox-url>/api/v1/projects/<project-id>/badge.svg?subject=<subject>&job_name=<job_name>&branch=<branch>
``` 

template         | meaning                   | optional
-----------------|---------------------------|----------
`<infrabox-url>` | InfraBox service url.     | False
`<project-id>`   | Project ID for api access | False
`<subject>`      | badge subject             | False
`<job_name>`     | full-qualified job name   | False
`<branch>`       | git branch                | True
