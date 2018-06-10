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
Give it a name (i.e. InfraBox), select a Zone and use a Kubernetes version 1.9.x. You should choose a machine type with at least 2 vCPU.
A cluster size of 2 nodes is sufficient for a test, but you may have to increase it later if you want to run more jobs in parallel.

You may keep the default values for the other options.
As soon as your cluster has been created click on connect and follow the instructions.

If you want to use the kubernetes dashboard you may have to give the service account more permissions:

```bash
kubectl create clusterrolebinding dashboard --clusterrole=cluster-admin --serviceaccount=kube-system:default
```

## Configure prerequisuites

### helm
We use [helm][helm] to deploy the different components. To install helm into you kubernetes cluster run:

```bash
kubectl -n kube-system create sa tiller
kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller
helm init --service-account tiller
```

### nginx ingress controller
Currently InfraBox only supports an nginx-ingress controller. To add one to your cluster:

```bash
helm install \
    -n nginx-ingress-controller \
    --namespace kube-system \
    --set rbac.create=true \
    --set controller.service.loadBalancerIP="<INSERT_YOUR_EXTERNAL_IP_HERE>" \
    --set controller.scope.enabled="true" \
    --set controller.scope.namespace="infrabox-system" \
    stable/nginx-ingress
```

**Don't forget to add your external IP address, which you have created earlier, as loadBalancerIP**

### Create namespaces
InfraBox seperates the control plane (dashboard, docker-registry, api server, etc) from the actual jobs. Create two namespaces:

```bash
kubectl create ns infrabox-system
kubectl create ns infrabox-worker
```

### Create TLS certificate
InfraBox requires a valid TLS certificate. It must be stored as a `Secret` with name `infrabox-tls-certs` in the `infrabox-system` namespace.

You have multiple options to create one:

- [Self signed certificates (not recommended, ok for testing, easiest to get started)](/docs/install/tls/self_signed.md)
- [Set an already existing certificate](/docs/install/tls/existing_certificate.md)
- [Use cert-manager to issue a certificate](/docs/install/tls/cert_manager.md)

### Storage
InfraBox requires an object store to persist some data like inputs/outpus, caches and as storage for the docker-registry. Chose one of the options:

- [Google Cloud Storage (recommended on GCP)](/docs/install/storage/gcs.md)
- [S3](/docs/install/storage/s3.md)
- [Minio](/docs/install/storage/minio.md)
- [Azure](/docs/install/storage/azure.md)

### Install PostgreSQL
InfraBox requires a PostgreSQL Database for persisting some data. You have the following options:

- [Deploy in Kubernetes (not recommended, ok for testing, easiest to get started)](/docs/install/storage/deploy_postgres.md)
- [CloudSQL](/docs/install/storage/cloudsql.md)
- [Connect to any PostgreSQL database](/docs/install/storage/postgres.md)

### Configure Authentication
You can configure different ways of how your user can authenticate.

- [GitHub (Use this if you want to connect your GitHub repositories)](/docs/install/configure/github.md)
- [Manual signup / login](/docs/install/configure/signup.md)

## Clone InfraBox repository
If you have not already cloned the InfraBox repository and checkout the version you would like to install.

```bash
git clone https://github.com/SAP/infrabox /tmp/infrabox
cd /tmp/infrabox
git checkout master
```

## Generate RSA Key
InfraBox uses a RSA key to sign certain information for security reasons. You need to generate a RSA key and keep it at a secure place

```bash
mkdir /tmp/infrabox-config
cd /tmp/infrabox-config
ssh-keygen -N '' -t rsa -f id_rsa
ssh-keygen -f id_rsa.pub -e -m pem > id_rsa.pem
```

## Configure InfraBox

InfraBox uses `helm` for deploying. Create a `my_values.yaml` for your custom options:

```bash
cat >my_values.yaml <<EOL
admin:
  private_key: $(base64 -w 0 ./id_rsa)
  public_key: $(base64 -w 0 ./id_rsa.pem)
EOL
```

Add all the necessary configurations options as described in the earlier steps.
If you forget some the installation will fail with some message like `a.b.c is required`.
After you have prepared your `my_values.yaml` you may deploy InfraBox.

```bash
helm install --namespace infrabox-system -f my_values.yaml --wait /tmp/infrabox/deploy/infrabox
helm install --namespace infrabox-system -f my_values.yaml --wait /tmp/infrabox/deploy/infrabox-function
```
After a few seconds you can open your browser and access `https://<YOUR_DOMAIN>`.

[helm]: https://github.com/kubernetes/helm
[minio]: https://www.minio.io/
