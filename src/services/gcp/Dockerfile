FROM golang:1.14-alpine AS build-env

RUN apk add --no-cache git curl bash
RUN curl https://raw.githubusercontent.com/golang/dep/master/install.sh | sh

COPY . /go/src/github.com/sap/infrabox/

WORKDIR /go/src/github.com/sap/infrabox/src/services/gcp

ENV GO111MODULE=off

RUN dep ensure
RUN ./tmp/build/build.sh

FROM alpine:3.7
ENV CLOUD_SDK_VERSION 330.0.0

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
    gcloud components install kubectl && \
    gcloud --version && \
    gcloud components install beta

WORKDIR /app
COPY --from=build-env /go/src/github.com/sap/infrabox/src/services/gcp/tmp/_output/bin/gcp /app/gcp

RUN addgroup -S infrabox && adduser -S -G infrabox infrabox
USER infrabox

ENTRYPOINT ./gcp
