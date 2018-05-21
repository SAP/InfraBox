# Azure Storage

Before you configure infrabox with Azure Storage, you need the following steps first.

- create a storage account
- create two containers(names: infrabox, registry) under the storage account

After that you can configure Azure Storage with `install.py` parameters:
```shell
  --storage azure
  --azure-account-name AZURE_ACCOUNT_NAME
  --azure-account-key AZURE_ACCOUNT_KEY
```
