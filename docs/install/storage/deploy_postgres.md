# Deploy Postgres
To install a PostgreSQL database in kubernetes simply run:

```bash
    helm install -n postgres --namespace infrabox-system --set postgresPassword=qweasdzxc1,postgresUser=infrabox,postgresDatabase=infrabox stable/postgresql
```

**This is not meant for production**

When configuring the InfraBox installation with `helm` use these options:

```yaml
database:
    postgres:
        enabled: true

        # Host of your postgres database
        host: postgres-postgresql.infrabox-system

        # Port of your postgres database
        port: 5432

        # Database name
        db: infrabox

        # Username
        username: infrabox

        # Password
        password: qweasdzxc1
```
