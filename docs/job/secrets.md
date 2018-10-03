# Secrets
InfraBox can store secret values for you, so you don't have to store passwords or other secret values in your repository. Login to the InfraBox Dashboard, select your project and go to the Settings tab. There you can create a secret with a name and value.

## Using secrets as environment variable
If you have created a [secret](#secrets) you can make it available as a environment variable.

```json
{
    "version": 1,
    "jobs": [{
        ...
        "environment": {
            "SOME_SECRET_VALUE": { "$secret": "NAME_OF_THE_SECRET" },
        }
    }]
}
```
