# Kubernetes
InfraBox runs on Kubernetes. So you can either use an already hosted kubernetes from Google or other vendors or set it up on your own machines. Please see the Kubernetes documentation on how to do this. For this guide we expect you have a running kubernetes installation somewhere.

## Create namespaces
InfraBox requires two namespaces:

    kubectl create namespace infrabox-system
    kubectl create namespace infrabox-worker

## Prepare helm
InfraBox will be later installed using helm. So make sure you have helm downloaded and configured:

    helm init

Maybe it's necessry to fix some RBAC things:

    kubectl create serviceaccount --namespace kube-system tiller
    kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
    kubectl patch deploy --namespace kube-system tiller-deploy -p '{"spec":{"template":{"spec":{"serviceAccount":"tiller"}}}}'

