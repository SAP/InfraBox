# Install Minio
[Minio][minio] is S3 compatible storage. We use it as storage for the internal docker registry as well as for storing caches, input/outup.

    $ helm install stable/minio --set serviceType=ClusterIP --namespace infrabox-system -n minio

**This configuration is not for production use**

If you want to setup minio for a production setup please read the minio guide how to do it.
You may also use S3 directly or any other S3 API compatible storage. [See S3 configuration](configure/s3.md) for the configuration options.

After minio has been started create a `Job` to initalize the minio bucket:

    apiVersion: batch/v1
    kind: Job
    metadata:
        name: init-minio
        namespace: infrabox-system
    spec:
        template:
            metadata:
                name: init-minio
            spec:
                containers:
                -
                    name: init-minio
                    image: minio/mc
                    command: ["/bin/sh", "-c"]
                    args: ["mc config host add infrabox http://minio-minio-svc.infrabox-system:9000 AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY S3v4 && mc mb infrabox/infrabox && mc ls infrabox"]
                restartPolicy: Never

Save it to minio-init.yaml and run:

    kubectl create -f minio-init.yaml


When configuring InfraBox later with `install.py` use these options:

    --storage s3
    --s3-access-key AKIAIOSFODNN7EXAMPLE
    --s3-secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    --s3-secure false
    --s3-endpoint minio-minio-svc.infrabox-system
    --s3-port 9000
    --s3-region us-east-1

