# Monitoring

We use prometheus for our monitoring. Install the [prometheus operator](https://github.com/coreos/prometheus-operator):

```bash
helm repo add coreos https://s3-eu-west-1.amazonaws.com/coreos-charts/stable/
helm install coreos/prometheus-operator --name prometheus-operator --namespace infrabox-system
```

When configuring your InfraBox with `helm` set these options:

```yaml
monitoring:
    enabled: true
```
