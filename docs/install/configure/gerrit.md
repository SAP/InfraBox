# Configure Gerrit
To access gerrit InfraBox needs some credentials. You need the private key with which InfraBox can connect to gerrit.

```yaml
gerrit:
    # Enable gerrit
    enabled: true

    # Gerrit Hostname
    hostname: # <REQUIRED>

    # Username
    username: # <REQUIRED>

    # base64 encoded private key for connecting to gerrit
    private_key: # <REQUIRED>

    # Port
    port: 29418
```
