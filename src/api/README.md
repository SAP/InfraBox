# API
The API Component implements the API for *infraboxcli* and the running *jobs*.

## Run tests
```bash
infrabox run ib # Only required once
infrabox run ib/test/api
```

## Start with dummy data
For development purposes you may want to start the API with some dummy data. Make sure you have setup  your development environment like described in [our developer guide](/docs/dev.md).

First start `postgres` and `minio` with some [dummy data](/infrabox/utils/storage):

```bash
./ib.py services start storage
```

Then start `opa` and push the policies to `opa`:
```bash
./ib.py services start opa
```

Now start the API:

```bash
./ib.py services start api
```

The API Server starts up on port 8080.

## API Docs
After you have started the API you can access the docs at http://localhost:8080/doc
