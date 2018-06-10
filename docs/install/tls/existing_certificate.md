# Existing certificate
If you already have a certificate for your domain you can simply create a `Secret` for it:

```bash
kubectl create -n infrabox-system secret tls infrabox-tls-certs --key <PATH_TO_KEY>.key --cert <PATH_TO_CRT>.crt
```

**The certificate must be signed by a trusted Root CA!**. If this is not the case for you certificate please see [how to use a self signed certificate](/docs/tls/self_signed.md).
