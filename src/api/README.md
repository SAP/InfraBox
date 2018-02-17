# API
[![coverage](https://infrabox.ninja/api/v1/projects/0c8204bb-7ce5-48a3-aa08-0fc38d7255d0/badge.svg?subject=coverage&job_name=ib/test/api)](https://infrabox.ninja/dashboard/#/project/infrabox)

The API Component implements the API for *infraboxcli* and the running *jobs*.

## Run tests
```
    $ infraboxcli run ib/test/api
```

## Start with dummy data
For development purposes you may want to start the API with some dummy data.
Make sure you started minio and postgres like described [here](/infrabox/utils/storage).

```
    $ ./run_with_dummy.sh
```

The API Server starts up on port 8080.

## API Docs
After you have started the API you can access the docs at http://localhost:8080
