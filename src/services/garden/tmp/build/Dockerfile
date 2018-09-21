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
        git

WORKDIR /app
ADD tmp/_output/bin/garden /app/garden

ENTRYPOINT ./garden
