# Install InfraBox on GCP with Deployment Manager

This guide shows you how to install InfraBox on GKE using Google Cloud Deployment Manager.

## Prerequisites
- This sample requires a valid Google Cloud Platform project with billing enabled. If you are not an existing GCP user, you may be able to enroll for a $300 US Free Trial credit.
- Ensure that the _Google Kubernetes Engine API_ and _Google Cloud Runtime Configuration API_ are enabled for your project (Check "API & Services" -> "Dashboard").
- You must install and configure the gcloud command line tool and include the kubectl component (gcloud components install kubectl).
- You need a domain like _infrabox.example.com_ with access to the DNS configuration

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
zone|true|Zone in which the Cluster will be created. It must be the same zone as your static external IP!
initialNodeCount|true|Number of Nodes in the GKE cluster
instanceType|true|Instance types of the nodes in the GKE cluster
domainName|true|Your domain under which your InfraBox installation will be accessible (i.e. _infrabox.example.com_)
githubEnabled|true|Set to true to allow login with github.com accounts. If set to false you have to manual register with email/password and you cannot connect GitHub Repositories
githubClientID|required if githubEnabled=true|Your GitHub oAuth Client ID you created earlier
githubClientSecret|required if githubEnabled=true|Your GitHub oAuth Client Secret you created earlier
githubLoginAllowedOrganizationsEnabled|required if githubEnabled=true|Set it to true if you want to limit the login to useres which belong to a particular list of GitHub Organizations. If set to false everybody with a GitHub account may login.
githubLoginAllowedOrganizations|required if githubLoginAllowedOrganizationsEnabled=true|Comma separated list of GitHub Organizations. Only user being in one of the Organizations may login

After you have modified the _infrabox.yaml_  you can create the deployment

```
gcloud deployment-manager deployments create my-infrabox --config=infrabox.yaml
```

In the following commands we will refer to <DEPLOYMENT_NAME>, in this case we are using _my-infrabox_ as name for our deployment. Wait until the deployment has been created. This may take 5-10 minutes.

A new Service Account has been created for accessing Google Cloud Storage. You have to give it proper permission, otherwhise InfraBox will not work:

```
    gcloud projects add-iam-policy-binding <PROJECT_NAME> --member="serviceAccount:<DEPLOYMENT_NAME>-sa@<PROJECT_NAME>.iam.gserviceaccount.com" --role='roles/storage.admin'
```
Now you should have a running InfraBox installation, but you still have to configure your DNS so your domain resolves to the LoadBalancer's IP.
Get the IP:

```
gcloud container clusters get-credentials <DEPLOYMENT_NAME> --zone <ZONE> --project <PROJECT_ID>
kubectl get svc -n kube-system | grep nginx-ingress-controller-controller | awk '{ print $4 }'
```

Now update your DNS for your domain to point to the external IP of the nginx-ingress-controller service.
_Please also read the following section on how to update the TLS certificates._

After a few minutes you should be able to access your InfraBox installation at https://<YOUR_DOMAIN>/.

## Download configuration
The installation creates a GCS bucket with all the configuration. You may use it to update/reconfigure your InfraBox installation. To download the configuration:

```
gsutil cp -r gs://<PROJECT_ID>-<DEPLOYMENT_NAME>-config/ .
```

## TLS Certificates
IMPORTANT_: After the installation you should replace the self signed certificate with a real one. If you don't do this then the GitHub webhooks won't work. If you don't want to replace the certificates you have to manually "Disable SSL Verification" for each webhook, after you connected your repository to InfraBox.

### Replace with already existing certificate
If you have already a certificate you can replace it with yours.

```
kubectl delete secret -n infrabox-system infrabox-tls-certs
kubectl create -n infrabox-system secret tls infrabox-tls-certs --key /path/to/tls.key --cert /path/to/tls.crt
```

And restart the nginx-ingress-controller pod in the kube-system namespace.
