FROM ubuntu:18.04
ARG HELM_VERSION=3.11.2

RUN apt-get update -y && apt-get install -y \
    curl \
    python3.8 \
    python3-pip \
    git

RUN mkdir /project
WORKDIR /project

RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl && \
    chmod +x /project/kubectl

RUN curl -LO https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz && \
    tar xvf helm-v${HELM_VERSION}-linux-amd64.tar.gz && \
    mv ./linux-amd64/helm ./helm && \
    rm -rf linux-amd64 && \
    rm helm-v${HELM_VERSION}-linux-amd64.tar.gz && \
    ls -al /project

ENV PATH=$PATH:/project
ENV PYTHONPATH=/infrabox/context/src

CMD /infrabox/context/infrabox/test/e2e/entrypoint.sh
