# Elastic Search & Kibana

Label all nodes:

    kubectl label nodes <NODE> beta.kubernetes.io/fluentd-ds-ready=true

Install it:

    clone kubernetes
    cd kubernetes/cluster/addons/fluentd-elasticsearch

    # maybe add a nodePort to kibana service

    kubectl create -f .

# Prometheus

Install the prometheus-operator

    clone prometheus-operator
    cd prometheus-operator/contrib/kube-prometheus
    ./hack/cluster-monitoring/deploy

Install InfraBox monitoring

    cd deploy/infrabox-monitoring
    helm install -n infrabox-monitoring .
