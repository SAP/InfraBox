# Install Minio
[Minio][minio] is S3 compatible storage. We use it as storage for the internal docker registry as well as for storing caches, input/outup.

```bash
    helm install stable/minio --set serviceType=ClusterIP --namespace infrabox-system -n minio
```

**This configuration is not for production use**

If you want to setup minio for a production setup please read the minio guide how to do it.
You may also use S3 directly or any other S3 API compatible storage. [See S3 configuration](configure/s3.md) for the configuration options.

When configuring InfraBox later with `helm` use these options:

```yaml
storage:
    s3:
        # Enabled S3
        enabled: true

        # Region
        region: us-east-1

        # Regeion endpoint
        endpoint: minio.infrabox-system

        # Region endpoint port
        port: 9000

        # If https should be used or not
        secure: false

        # Bucket name
        bucket: infrabox

        # AWS Access Key ID
        access_key_id: AKIAIOSFODNN7EXAMPLE

        # AWS Secret Access Key
        secret_access_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```
