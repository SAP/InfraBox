# InfraBox Local Dev Stack

A Docker Compose environment for running the full backend stack locally,
including PostgreSQL, MinIO, OPA, and the API server.

## Quick Start

```bash
cd infrabox/local-dev

# 1. Create your local config (only needed once)
cp .env.example .env
#    Edit .env and set INFRABOX_DB_PASSWORD to any value you like.

# 2. Start the backend stack
make start

# 3. Start the frontend dev server (separate terminal)
make frontend
```

Open http://localhost:8081 (increments automatically if 8080 is taken).

**Default credentials** (created by `seed.sql` on first run):

| Email | Password | Role |
|-------|----------|------|
| admin@local.dev | admin123 | admin |

Log in with the **email** address, not the username.

## Other Commands

```bash
make logs    # tail API logs
make stop    # tear down all containers
```

## How It Works

- `seed.sql` is mounted into the postgres container and runs on first startup.
  It inserts the required `cluster` row and the default admin user.
- The API is exposed on host port `8090` (container port `8080`).
- API requests from the frontend dev server are proxied to `http://localhost:8090`
  via the webpack `proxyTable` — no manual CORS configuration needed.
- RSA keys are reused from `infrabox/test/utils/id_rsa[.pub]` — local dev only.
- OPA and API are built from source to pick up the latest policies and handlers.

## Adding More Users

```bash
# Generate a bcrypt hash for any password
python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"

docker exec local-dev-postgres-1 psql -U postgres -c "
  INSERT INTO \"user\" (username, email, password, role)
  VALUES ('alice', 'alice@example.com', '<bcrypt-hash>', 'user');
"
```
