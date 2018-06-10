# Azure Storage

Before you configure infrabox with Azure Storage, you need the following steps first.

- create a storage account
- create two containers(names: infrabox, registry) under the storage account

After that you can configure Azure Storage with `helm` parameters:

```yaml
storage:
    azure:
        # Enable Azure
        enabled: false

        # Account name
        account_name: # <REQUIRED>

        # Account key
        account_key: # <REQUIRED>
```
