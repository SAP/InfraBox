FROM docker:17.12.1-ce-dind

ENV CLOUD_SDK_VERSION 210.0.0
ENV PATH /google-cloud-sdk/bin:$PATH

RUN apk add --no-cache \
    python \
    python-dev \
    py-pip \
    py-requests \
    py-crcmod \
    g++ \
    pv \
    snappy-dev \
    bash \
    curl \
    bash \
    libc6-compat \
    openssh-client \
    git && \
    pip install docker==2.0.1 awscli pyyaml && \
    pip install docker-compose==1.20.1 future PyJWT python-snappy && \
    apk del py-pip python-dev g++ && \
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    tar xzf google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    rm google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    ln -s /lib /lib64 && \
    gcloud config set core/disable_usage_reporting true && \
    gcloud config set component_manager/disable_update_check true && \
    gcloud config set metrics/environment github_docker_image && \
    gcloud --version

COPY src/job /job

COPY src/job/ecr_login.sh /usr/local/bin/
COPY src/job/get_compose_exit_code.sh /usr/local/bin/
COPY src/job/entrypoint.sh /usr/local/bin/

COPY src/pyinfrabox /pyinfrabox
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/utils:/
ENV PATH=/utils:$PATH

RUN chmod +x /usr/local/bin/entrypoint.sh
CMD /usr/local/bin/entrypoint.sh
