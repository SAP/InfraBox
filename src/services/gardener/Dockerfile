FROM golang:1.10-alpine AS build-env

RUN apk add --no-cache git curl bash
RUN curl https://raw.githubusercontent.com/golang/dep/master/install.sh | sh

COPY . /go/src/github.com/sap/infrabox/

WORKDIR /go/src/github.com/sap/infrabox/src/services/gardener

RUN dep ensure
RUN ./tmp/build/build.sh

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
COPY --from=build-env /go/src/github.com/sap/infrabox/src/services/gardener/tmp/_output/bin/gardener /app/gardener

RUN addgroup -S infrabox && adduser -S -G infrabox infrabox
USER infrabox

ENTRYPOINT ./gardener
