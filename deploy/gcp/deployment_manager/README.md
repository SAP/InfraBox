# Install InfraBox on GCP with Deployment Manager

This guide shows you how to install InfraBox on GKE using Google Cloud Deployment Manager.

## Prerequisites
- This sample requires a valid Google Cloud Platform project with billing enabled. If you are not an existing GCP user, you may be able to enroll for a $300 US Free Trial credit.
- Ensure that the _Google Kubernetes Engine API_ and _Google Cloud Runtime Configuration API_ are enabled for your project (Check "API & Services" -> "Dashboard").
- You must install and configure the gcloud command line tool and include the kubectl component (gcloud components install kubectl).
- You need a domain like _infrabox.example.com_ with access to the DNS configuration

## Configure DNS
First we have to create a static external IP. InfraBox will use this IP for its load balancer.

```
    $ gcloud compute addresses create infrabox-lb --region us-central1
```

You may choose a different region. The region must match the region you want to run you InfraBox installation in.
To get the actul IP run:

```
    $ gcloud compute addresses describe infrabox-lb --region us-central1 | grep address:
```

Remeber the IP, you will later need. Now update your DNS for you domain (i.e. _infrabox.example.com_) to point the IP you just created.

## Create Github App
This step is optional, but if you want to run builds for projects hosted on github.com you should create a GitHub application.
Login to github.com and go to Settings -> Developer Settings -> New OAuth App. Enter these values:

- Application name: InfraBox
- Homepate URL: https://infrabox.net
- Authorization callback URL: https://<YOUR_DOMAIN>/github/auth/callback (i.e. https://infrabox.example.com/github/auth/callback)

Remember the _Client ID_ and _Client Secret_.

## Configure Deployment
Edit the infrabox.yaml and set the properties.

Property | Required | Description
---------|----------|------------
gkeClusterName|true|Name of the GKE Cluster which will be created
zone|true|Zone in which the Cluster will be created. It must be the same zone as your static external IP!
initialNodeCount|true|Number of Nodes in the GKE cluster
instanceType|true|Instance types of the nodes in the GKE cluster
domainName|true|Your domain under which your InfraBox installation will be accessible (i.e. _infrabox.example.com_)
externalLBIP|true|External static IP you created earlier. Your domain has to resolve to this IP.
dockerRegistryPassword|true|Choose a password for the internal Docker Registry
githubEnabled|false|Set to true to allow login with github.com accounts. If set to false use have to manual register with email/password and you cannot connect GitHub Repositories.
githubClientID|required if githubEnabled=true|Your GitHub oAuth Client ID you created earlier
githubClientSecret|required if githubEnabled=true|Your GitHub oAuth Client Secret you created earlier
githubLoginAllowedOrganizationsEnabled|required if githubEnabled=true|Set it to true if you want to limit the login to useres which belong to a particular list of GitHub Organizations. If set to false everybody with a GitHub account may login.
githubLoginAllowedOrganizations|required if githubLoginAllowedOrganizationsEnabled=true|Comma separated list of GitHub Organizations. Only user being in one of the Organizations may login

After you have modified the _infrabox.yaml_  you can create the deployment

```
    $ gcloud deployment-manager deployments create my-infrabox --config=infrabox.yaml
```

After 5-10 minutes you should have a running InfraBox installation accessible at _https://<your\_domain>_.

_IMPORTANT_: After the installation you should replace the self signed certificate with a real one. If you don't do this then the GitHub webhooks won't work. If you don't want to replace the certificates you have to manually "Disable SSL Verification" for each webhook, after you connected your repository to InfraBox.

## TLS Certificates
The installation creates a self signed certificate. You should replace it with a real certificate.

### Replace with already existing certificate
If you have already a certificate you can replace it with yours.

```
    $ kubectl delete secret -n infrabox-system infrabox-tls-certs
    $ kubectl create -n infrabox-system secret tls infrabox-tls-certs --key /path/to/tls.key --cert /path/to/tls.crt
```

And restart the nginx-ingress-controller pod in the kube-system namespace.

### Let's Encrypt
You can also use let's encrypt to get a certificate for you domain.

TODO
