FROM stege/baseimage-gcloud:1

# install kubectl
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
RUN mv ./kubectl /usr/local/bin/kubectl

# install helm
RUN curl https://storage.googleapis.com/kubernetes-helm/helm-v2.4.1-linux-amd64.tar.gz > /tmp/helm.tar.gz && \
    tar xvf /tmp/helm.tar.gz && \
    mv /linux-amd64/helm /usr/local/bin/helm && \
    rm /tmp/helm.tar.gz

# install pip
RUN apk add --no-cache py-pip git

COPY . project

CMD /project/infrabox/test-kubernetes/entrypoint.sh
