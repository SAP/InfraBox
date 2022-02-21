FROM docker:19.03.12-dind

ENV CLOUD_SDK_VERSION 298.0.0
ENV PATH /google-cloud-sdk/bin:$PATH

RUN apk add --no-cache \
    python3 \
    python3-dev \
    py3-jwt \
    py3-pip \
    py-requests \
    py-crcmod \
    g++ \
    pv \
    snappy-dev \
    curl \
    bash \
    libc6-compat \
    openssh-client \
    git && \
    pip3 install docker awscli pyyaml docker-compose && \
    pip3 install future python-snappy && \
    apk del py-pip python3-dev g++ && \
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    tar xzf google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    rm google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    ln -s /lib /lib64 && \
    gcloud config set core/disable_usage_reporting true && \
    gcloud config set component_manager/disable_update_check true && \
    gcloud config set metrics/environment github_docker_image && \
    gcloud --version

ADD http://aia.pki.co.sap.com/aia/SAP%20Global%20Root%20CA.crt \
    /usr/local/share/ca-certificates/
RUN update-ca-certificates
COPY src/job /job

COPY src/job/ecr_login.sh /usr/local/bin/
COPY src/job/entrypoint.sh /usr/local/bin/

COPY src/pyinfrabox /pyinfrabox
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/utils:/
ENV PATH=/utils:$PATH

ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]
