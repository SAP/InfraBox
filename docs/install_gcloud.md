# Install InfraBox on Google Cloud Platform
For this guide you should have some basic experience with GCP. If you don't have a Google Cloud Platform account then you can create one for free. You will also receive 300$ which you can spend on GCP services.

## Prerequisites
- [A GCP Account](https://cloud.google.com/?hl=en)
- [docker](https://www.docker.com/)
- [helm][helm]
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- a domain with access to the DNS configuration (i.e. `infrabox.example.com`)

## Setup your GCP Account
A few things need to be created before we can install InfraBox.

### External IP address
To make your InfraBox installation available externally you need an IP address.
You may create one in the GCP Console under "VPC Network" -> "External IP addresses".
Give it a name, select IPv4 and Type Regional and a region. Your kubernetes cluster should be created in the same region later on.

### Configure DNS
Configure your DNS to point to the external IP address.

### Create a Kubernetes cluster
InfraBox runs on Kubernetes. So we have to create a cluster first. In the GCP Console go to "Kubernetes Engine" and create a cluster.
Give it a name (i.e. InfraBox), select a Zone and use a Kubernetes version 1.7.x. You should choose a machine type with at least 2 vCPU.
A cluster size of 2 nodes is sufficient for a test, but you may have to increase it later if you want to run more jobs in parallel.

**Important: Set "Legacy Authorization" to disabled**

You may keep the default values for the other options.
As soon as your cluster has been created click on connect and follow the instructions.

If you want to use the kubernetes dashboard you may have to give the service account more permissions:

    $ kubectl create clusterrolebinding dashboard --clusterrole=cluster-admin --serviceaccount=kube-system:default

## Configure prerequisuites

### helm
We use [helm][helm] to deploy the different components. To install helm into you kubernetes cluster run:

    $ kubectl -n kube-system create sa tiller
    $ kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
    $ helm init --service-account tiller

### Create namespaces
InfraBox seperates the controle plane (dashboard, docker-registry, api server, etc) from the actual jobs. Create two namespaces:

    $ kubectl create ns infrabox-system
    $ kubectl create ns infrabox-worker

### nginx ingress controller
Currently InfraBox only supports an nginx-ingress controller. To add one to your cluster:

    helm install \
        -n nginx-ingress-controller \
        --namespace kube-system \
        --set rbac.create=true \
        --set controller.service.loadBalancerIP=<INSERT_YOUR_EXTERNAL_IP_HERE> \
        --set controller.config.proxy-body-size="0" \
        stable/nginx-ingress

**Don't forget to add your external IP address, which you have created earlier, as loadBalancerIP**

### Create TLS certificate
If you already have a certificate for your domain you may skip this.

    $ openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /tmp/tls.key -out /tmp/tls.crt -subj "/CN=infrabox.example.com"

Now create a Kubernetes secret for the certificate:

    $ kubectl create secret tls infrabox-tls-certs --key /tmp/tls.key --cert /tmp/tls.crt

### Install Minio
[Minio][minio] is S3 compatible storage. We use it as storage for the internal docker registry as well as for storing caches, input/outup

    $ helm install stable/minio --set serviceType=ClusterIP --namespace infrabox-system -n minio

**This configuration is not for production use**

If you want to setup minio for a production setup please read the minio guide how to do it.
You may also use S3 directly or any other S3 API compatible storage. [See S3 configuration](configure/s3.md) for the configuration options.

After minio has been started create a Job to initalize the minio buckets:

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
                    args: ["mc config host add infrabox http://minio-minio-svc.infrabox-system:9000 AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY S3v4 && mc mb infrabox/infrabox-container-output && mc mb infrabox/infrabox-project-upload && mc mb infrabox/infrabox-container-content-cache && mc mb infrabox/infrabox-docker-registry && mc ls infrabox"]
                restartPolicy: Never

Save it to minio-init.yaml and run:

    kubectl create -f minio-init.yaml

### Install PostgreSQL
To install a PostgreSQL database in kubernetes simply run:

    helm install -n postgres --namespace infrabox-system --set postgresPassword=qweasdzxc1,postgresUser=infrabox,postgresDatabase=infrabox stable/postgresql

**This is also not meant for production**

You can use any PostgreSQL 9.6 database. See [Configuring PostgreSQL](configure/postgres.md) for the available options.

## Clone InfraBox repository
If you have not already cloned the InfraBox repository do so with:

    $ git clone https://github.com/infrabox/infrabox /tmp/infrabox

## Generate RSA Key
InfraBox uses a RSA key to sign certain information for security reasons. You need to generate a RSA key and keep it at a secure place

    ssh-keygen -N '' -t rsa -f id_rsa

## Configure InfraBox
InfraBox contains a python script to generate all the neccessary configuration files for you. You find it under _deplpy/install.py_.
To create a very basic configuration use (don't forget to insert your external IP address!):

    $ python deploy/install.py \
        -o /tmp/infrabox-configuration \
        --platform kubernetes \
        --general-rsa-public-key ./id_rsa.pub \
        --general-rsa-private-key ./id_rsa \
        --root-url https://infrabox.example.com \
        --general-dont-check-certificates \
        --database postgres \
        --postgres-host postgres-postgresql.infrabox-system \
        --postgres-username infrabox \
        --postgres-database infrabox \
        --postgres-port 5432 \
        --postgres-password qweasdzxc1 \
        --storage s3 \
        --s3-access-key AKIAIOSFODNN7EXAMPLE \
        --s3-secret-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
        --s3-secure false \
        --s3-endpoint minio-minio-svc.infrabox-system \
        --s3-port 9000 \
        --s3-region us-east-1 \
        --docker-registry-admin-username admin \
        --docker-registry-admin-password admin \
        --dashboard-secret someothersecret \
        --account-signup-enabled

**Set --root-url to your domain name**

This command generated the neccessary files in `/tmp/infrabox-configuration`.

### Options

    --docker-registry-admin-username admin
    --docker-registry-admin-password admin

This is the admin username and password which you can use to login to InfraBox's internal docker registry. Keep them secret, because you will have full access to the registry.

    --general-dont-check-certificates

With this option the hosted docker registry will be marked as insecure and HTTPS certificates will not be checked.
Remove this option if you have used a TLS certificate has been signed by a CA.

### Deploy InfraBox
To deploy InfraBox:

    $ cd /tmp/infrabox-configuration/infrabox
    $ helm install -n infrabox .

After a few seconds you can open your browser and access `https://infrabox.example.com`.

[helm]: https://github.com/kubernetes/helm
[minio]: https://www.minio.io/
