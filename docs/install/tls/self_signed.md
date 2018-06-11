# Self signed TLS Certificate
This is ok for testing, but not recommended for production (replace `infrabox.example.com` with your domain):

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /tmp/tls.key -out /tmp/tls.crt -subj "/CN=infrabox.example.com"
```

Now create a Kubernetes secret for the certificate:

```bash
kubectl create -n infrabox-system secret tls infrabox-tls-certs --key /tmp/tls.key --cert /tmp/tls.crt
```

**It's important to pass the following option when installing with helm:**

```yaml
general:
    dont_check_certificates: false
job:
    docker_daemon_config: |-
        {"insecure-registries": ["infrabox.example.com"]}
```
