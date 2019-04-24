# Install InfraBox

![Install InfraBox](./install.gif)

## Quickstart on GKE
If you want to get something up and running quickly you can use `infraboxcli` to install InfraBox on a GKE Cluster.

All you need ist:
- [A GCP Account](https://cloud.google.com/?hl=en)
- [gcloud](https://cloud.google.com/sdk/install) installed and configured to create a kubernetes cluster in your project
- [helm](https://github.com/kubernetes/helm) installed
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) installed
- [git](https://git-scm.com/) installed
- [infraboxcli](https://github.com/sap/infrabox-cli)

Run `infrabox install` and follow the instructions.

# Manual Installation
You can run InfraBox on any Kubernetes Cluster with at least version 1.9.

## Prerequisites
- [helm][helm] (at least 2.10)
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- a domain with access to the DNS configuration (i.e. `infrabox.example.com`)

Create a Kubernetes Cluster:
- [Google Kubernetes Engine](./gke.md)
- [Azure Kubernetes Service](./aks.md)

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

### Configure Monitoring
You may optionally configure Grafana/Prometheus monitoring.

- [Configure Monitoring](/docs/install/configure/monitoring.md)

### Configure Status page
You may optionally configure a status page.

- [Cachet](/docs/install/configure/cachet.md)


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
ssh-keygen -t rsa -b 4096 -m PEM -f jwtRS256.key
openssl rsa -in jwtRS256.key -pubout -outform PEM -out jwtRS256.key.pub
```

## Configure InfraBox

InfraBox uses `helm` for deploying. Create a `my_values.yaml` for your custom options:

```bash
cat >my_values.yaml <<EOL
image:
  tag: 1.1.5 # chose a released version
admin:
  private_key: $(base64 -w 0 ./jwtRS256.key)
  public_key: $(base64 -w 0 ./jwtRS256.key.pub)
EOL
```

If you get an error `base64: invalid option -- w` (e.g. on macOS), change the `-w` to `-b` in the `base64` subcommand.

Add all the necessary configurations options as described in the earlier steps.
If you forget some the installation will fail with some message like `a.b.c is required`.
After you have prepared your `my_values.yaml` you may deploy InfraBox.

**IMPORTANT: This requires at least helm 2.10**

```bash
helm install --namespace infrabox-system -f my_values.yaml --wait /tmp/infrabox/deploy/infrabox
```
After a few seconds you can open your browser and access `https://<YOUR_DOMAIN>`.

[helm]: https://github.com/kubernetes/helm
[minio]: https://www.minio.io/


## HA mode
You can deploy multi cluster with [HA mode](/docs/install/ha_mode.md)

## Legal
You can provide a privacy and terms of use url. These links will show up in the footer.
