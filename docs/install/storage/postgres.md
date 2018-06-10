# Postgres
If you already have some PostgreSQL Database running somwhere you can simply pass the connection details to `helm`:

```yaml
database:
    postgres:
        enabled: true

        # Host of your postgres database
        host: # <REQUIRED>

        # Port of your postgres database
        port: 5432

        # Database name
        db: # <REQUIRED>

        # Username
        username: # <REQUIRED>

        # Password
        password: # <REQUIRED>
```
