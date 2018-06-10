# Google SQL Postgres
TODO link to create db...

```yaml
database:
    cloudsql:
        # Enable
        enabled: false

        # Database name
        db: # <REQUIRED>

        # Username
        username: # <REQUIRED>

        # Password
        password: # <REQUIRED>

        # The instance connection name
        instance_connection_name: # <REQUIRED>

        # base64 encoded service account .json file
        service_account: # <REQUIRED>
```
