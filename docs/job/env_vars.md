# Environment Variables
You can set environment variables in your job definition. They will be available during the run phase of the container, not during build.

```json
{
    "version": 1,
    "jobs": [{
        ...
        "environment": {
            "SOME_ENV_VAR": "My value",
            "ANOTHER_ENV_VAR": "Another value"
        }
    }]
}
```
