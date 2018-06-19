# Install InfraBox on Google Cloud Platform
For this guide you should have some basic experience with GCP. If you don't have a Google Cloud Platform account then you can create one for free. You will also receive 300$ which you can spend on GCP services.

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
