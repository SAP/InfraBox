# InfraBox Local Dev Stack

A Docker Compose environment for running the full backend stack locally,
including PostgreSQL, MinIO, OPA, and the API server.

## Before You Start

**Set passwords**: the password fields in `docker-compose.yml` are left blank.
Fill them in before starting:

```yaml
# postgres service
- POSTGRES_PASSWORD=<your-password>

# api service
- INFRABOX_DATABASE_PASSWORD=<your-password>   # must match the value above
```

Any simple password (e.g. `postgres`) works fine for local use.

## Start

```bash
# First run: builds API, OPA, and Postgres images from source
DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 \
  docker compose -f infrabox/local-dev/docker-compose.yml up -d

# Follow API logs
docker compose -f infrabox/local-dev/docker-compose.yml logs -f api
```

## Frontend Dev Server

```bash
cd src/dashboard-client
npm install --legacy-peer-deps --ignore-scripts
npm run dev
```

Open http://localhost:8081 (the port increments automatically if 8080 is taken).

API requests are forwarded to `http://localhost:8090` via the webpack proxyTable —
no manual CORS configuration needed.

## Create Test Users

```bash
# Generate a bcrypt password hash (requires the bcrypt Python package)
python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"

# Insert a user (role: 'user' or 'admin')
docker exec local-dev-postgres-1 psql -U postgres -c "
  INSERT INTO \"user\" (username, email, password, role)
  VALUES ('alice', 'alice@example.com', '<bcrypt-hash>', 'user');
"
```

Log in with the **email** address, not the username.

## Stop

```bash
docker compose -f infrabox/local-dev/docker-compose.yml down
```

## Notes

- `seed.sql` inserts the required `cluster` row on first startup
- The API is exposed on host port `8090` (container port `8080`)
- RSA keys are reused from `infrabox/test/utils/id_rsa[.pub]` — local dev only
- OPA and API are built from source to pick up the latest policies and handlers
