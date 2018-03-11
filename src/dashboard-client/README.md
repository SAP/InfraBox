# Dashbard

## Start with dummy data
For development purposes you may want to start the API with some dummy data. Make sure you have setup  your development environment like described in [our developer guide](/docs/dev.md).

First start `postgres` and `minio` with some [dummy data](/infrabox/test/utils/storage) as well as `api` and `dashboard-api`. Run each command in its own shell:

```bash
./ib.py services start storage
./ib.py services start api
./ib.py services start dashboard_api
```

To run the UI you have to allow cross origin requests. For chrome first close all instances of it and run it as:

```bash
chromium-browser --disable-web-security --user-data-dir
```

Now start the UI:

```bash
./ib.py services start dashboard-client
```

The dashboard starts up on port 8081.
