# API
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
