# Use cert-manager

This is only an example for the Let's Encrypt Staging. Please also read the [cert-manager documentation](https://github.com/jetstack/cert-manager/blob/master/docs/user-guides/acme-http-validation.md).

Create an `Issuer` (set the `email`):

```yaml
apiVersion: certmanager.k8s.io/v1alpha1
kind: Issuer
metadata:
  name: letsencrypt-staging
  namespace: infrabox-system
spec:
  acme:
    server: https://acme-staging.api.letsencrypt.org/directory
    email: user@infrabox.example.com # CHANGE
    privateKeySecretRef:
      name: letsencrypt-staging
    http01: {}
```

Create the `Certificate`:

```yaml
apiVersion: certmanager.k8s.io/v1alpha1
kind: Certificate
metadata:
  name: infrabox
  namespace: infrabox-system # Don't change
spec:
  secretName: infrabox-tls-certs # Don't change
  issuerRef:
    name: letsencrypt-staging
  commonName: <YOUR_DOMAIN, i.e. infrabox.example.com>
  acme:
    config:
    - http01:
        ingressClass: nginx # Don't change
      domains:
      - <YOUR_DOMAIN, i.e. infrabox.example.com>
```

Wait until the `Certificate` has been issued successfully:

	kubectl describe certificate infrabox -n infrabox-system

