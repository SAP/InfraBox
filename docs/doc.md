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
|jobs|true|array of job definitions|A list of the actual jobs to run. It can be either<ul><li>[docker](/docs/job/docker.md)</li><li>[docker-image](/docs/job/docker_image.md)</li><li>[docker-compose](/docs/job/docker_compose.md)</li><li>[git](/docs/job/git.md)</li><li>[workflow](/docs/job/workflow.md)</li></ul>|

# Upload Test Result
InfraBox can show your testresult on a tab at the job detail view. This gives you the possibility to quickly check the results and if one of your tests has failed you can even see the error message and stacktrace if available. To use this feature you only have to copy your testresult file to `/infrabox/upload/testresult`. We will try to auto detect the format of your file. Currently supported file formats are:

- xunit (xml)

# Upload Coverage Result
InfraBox can show your coverage results on a tab at the job detail view. To use this feature you only have to copy your coverage file to `/infrabox/upload/coverage`. We will try to auto detect the format of your file. Currently supported file formats are:

- cobertura (xml)
- clover (xml)

# Dynamic Workflows
Often a pre-defined static workflow is not sufficient to handle all use cases. For this InfraBox supports dynamic workflows. Every job in your workflow may produce an `infrabox.json` in its output directory `/infrabox/output/infrabox.json`. All jobs defined in there will be automatically added as predecessor jobs. This give you the options to extend your workflow at runtime.

This feature is extremely useful for bigger projects. Maybe you don't want to run certain tests on a branch or you want to additionaly deploy your containers to an registry if you create a tag.

# Archive
Sometimes it's helpful to store some files for later access. Every file you write to `/infrabox/upload/archive` will later be accessible in the Dashboard for the job.

