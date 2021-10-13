# Monitoring

We use prometheus for our monitoring. 

Install the [prometheus operator](https://github.com/prometheus-operator/prometheus-operator) by following their official documentation.


When configuring your InfraBox with `helm` set these options:

```yaml
monitoring:
    enabled: true
```
