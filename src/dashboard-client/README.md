# Dashboard

## Start with dummy data
For development purposes you may want to start the API with some dummy data. Make sure you have setup  your development environment like described in [our developer guide](/docs/dev.md).

Go to the root folder of the infrabox project.

First start `postgres` and `minio` with some [dummy data](/infrabox/test/utils/storage) as well as `api`. Run each command in its own shell:

```bash
./ib.py services start storage
./ib.py services start api
```

To run the UI you have to allow cross origin requests. For chrome first close all instances of it and run it as:

```bash
chromium-browser --disable-web-security --user-data-dir
```

Another way to handle cross origin is the usage of a reverse proxy to combine the api and dashboard http servers, e. g. nginx:

```
server {
  listen 80;
  listen [::]:80;
  server_name localhost;
  
  location / {
      proxy_pass http://localhost:8081/;
  }
  location /api {
    proxy_pass http://localhost:8080/api;
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
  }
  location /github {
    proxy_pass http://localhost:8080/github;
  }
}
```

Now start the UI:

```bash
./ib.py services start dashboard-client
```

The dashboard starts up on port 8081.
