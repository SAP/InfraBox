FROM golang:1.10-alpine AS build-env

RUN apk add --no-cache git bash curl
RUN curl https://glide.sh/get | sh

COPY . /go/src/github.com/infrabox/infrabox/

WORKDIR /go/src/github.com/infrabox/infrabox/src/services/gcp

RUN glide install
RUN ./hack/update-codegen.sh
RUN go build

FROM alpine:3.7
ENV CLOUD_SDK_VERSION 198.0.0

ENV PATH /google-cloud-sdk/bin:$PATH

RUN apk --no-cache add \
        curl \
        python \
        py-crcmod \
        bash \
        libc6-compat \
        openssh-client \
        git \
    && curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    tar xzf google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    rm google-cloud-sdk-${CLOUD_SDK_VERSION}-linux-x86_64.tar.gz && \
    ln -s /lib /lib64 && \
    gcloud config set core/disable_usage_reporting true && \
    gcloud config set component_manager/disable_update_check true && \
    gcloud config set metrics/environment github_docker_image && \
    gcloud config set container/use_v1_api false && \
    gcloud config set container/new_scopes_behavior true && \
    gcloud components install kubectl && \
    gcloud --version

WORKDIR /app
COPY --from=build-env /go/src/github.com/infrabox/infrabox/src/services/gcp/gcp /app/gcp

ENTRYPOINT ./gcp -logtostderr
