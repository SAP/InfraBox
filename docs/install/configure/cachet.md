# Cachet

To use [Cachet](https://cachethq.io/) as your status page you have to provide the following configuration:

```yaml
cachet:
    enabled: true
    endpoint: http://status.example.com/api/v1
    api_token: SomeApiToken
```

InfraBox will periodically update the status page.
