# Dependency Configuration
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

If the the parent job would create the file `/infrabox/output/hello_world.txt`, then the child job would be able to access it at run time (i.e. when the child job container is running) under `/infrabox/inputs/parent/hello_world.txt`. The file is also available at build time (i.e. when building a Docker image for the child job): Infrabox would add the file at `.infrabox/inputs/parent/hello_world.txt` on the repo root and it can be referenced on the child job's Dockerfile.
