# Vault(KV Engines only)
InfraBox can fetch values as environment from vault service, so if your variable rotation regularly, you can configure it with vault in your projects. You just need to update the variable in Vault rather than update in your Infrabox project when the variable rotation. Login to the InfraBox Dashboard, select your project and go to the Settings tab. There you can create a vault with a name, a url, a namespace, a version, a token, a ca certificate, a role_id and a secret_id.

## Parameters explanation

name: a DIY name (e.g. myvault)  

url: the url of vault service (e.g. https://vault-service.com:1234)  

namespace: the Vault's namespace, only enterprise edition enable namespace.  

version：Vault provide version 1 or 2 for KV engine. just set it with 1 or 2.

token: a token to access Vault.

ca: provide ca certificate if using https. This is not mandatory. But if you provide the certificate, don't remember to change it when certificate changes.

role_id: besides token, you could also use approle to access vault. With that way, you will create an approle in Vault, and role_id is a parameter of an approle.

secret_id: besides token, you could also use approle to access vault. With that way, you will create an approle in Vault, and role_id is a parameter of an approle.

Note that:
1) if token and approle provided at the same time, token will be used.

2) if token in empty, please provide role_id and secert_id at the same time.

## Using secrets as environment variable
If you have created a [vault](#vault) you can make it available as a environment variable.

```json
{
    "version": 1,
    "jobs": [{
        ...
        "environment": {
            "SOME_VALUE": {
                "$vault": " the name of the vault",
                "$vault_secret_path": "the secret path in vault's kv engine",
                "$vault_secret_key": "the key of the vault secret"
            },
        }
    }]
}
```
