FROM docker:20.10.14-dind

ENV CLOUD_SDK_VERSION 380.0.0
ENV PATH /google-cloud-sdk/bin:$PATH
RUN apk add --update --no-cache \
    clang-dev musl-dev yaml curl libmicrohttpd libuuid make
RUN mkdir deps && \
    wget -O - https://static.rust-lang.org/dist/rust-nightly-$(apk --print-arch)-unknown-linux-musl.tar.gz | tar -C deps -z -x -f - && \
    sh /deps/rust-nightly-$(apk --print-arch)-unknown-linux-musl/install.sh --prefix=/usr && \
    rm -rf /deps
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
    linux-headers \
    libffi-dev \
    gcc \
    musl-dev \
    openssl-dev \
    curl \
    bash \
    libc6-compat \
    git && \
    pip3 install pynacl docker awscli pyyaml && \
    pip3 install future python-snappy six
## Install openssh 8.3
RUN sed -i 's/v3.15/v3.12/g' /etc/apk/repositories && \
    apk add --update openssh-client
RUN curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    tar xzf google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    rm google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    ln -s /lib /lib64 && \
    gcloud config set core/disable_usage_reporting true && \
    gcloud config set component_manager/disable_update_check true && \
    gcloud config set metrics/environment github_docker_image && \
    gcloud --version

## Install latest docker-compose
RUN apk add jq && \
    DESTINATION=/usr/bin/docker-compose && \
    curl -L https://github.com/docker/compose/releases/download/v2.14.0/docker-compose-$(uname -s)-$(uname -m) -o $DESTINATION && \
    chmod 755 $DESTINATION

COPY src/job /job

COPY src/job/ecr_login.sh /usr/local/bin/
COPY src/job/entrypoint.sh /usr/local/bin/

COPY src/pyinfrabox /pyinfrabox
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/utils:/
ENV PATH=/utils:$PATH

ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]
