FROM ubuntu

RUN apt-get update -y && apt-get install -y curl python-pip postgresql-client
RUN mkdir /project
WORKDIR /project

RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl && \
    chmod +x /project/kubectl

RUN curl -LO https://storage.googleapis.com/kubernetes-helm/helm-v2.7.0-linux-amd64.tar.gz && \
    tar xvf helm-v2.7.0-linux-amd64.tar.gz && \
    mv ./linux-amd64/helm ./helm && \
    rm -rf linux-amd64 && \
    rm helm-v2.7.0-linux-amd64.tar.gz && \
    ls -al /project

ENV PATH=$PATH:/project

COPY . /test

CMD /test/entrypoint.sh
