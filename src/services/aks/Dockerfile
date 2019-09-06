FROM golang:1.10-alpine AS build-env

RUN apk add --no-cache git curl bash
RUN curl https://raw.githubusercontent.com/golang/dep/master/install.sh | sh

COPY . /go/src/github.com/sap/infrabox/

WORKDIR /go/src/github.com/sap/infrabox/src/services/aks

RUN dep ensure
RUN chmod +x ./tmp/build.sh
RUN ./tmp/build.sh

FROM alpine:3.7

ENV PATH $PATH:/usr/local/bin

RUN \
  apk update && \
  apk add bash py-pip libssl1.0 && \
  apk add --virtual=build linux-headers gcc libffi-dev musl-dev openssl-dev python-dev make && \
  pip install -U pip && \
  pip install azure-cli && \
  apk del --purge build && \
  az aks install-cli

WORKDIR /app
COPY --from=build-env /go/src/github.com/sap/infrabox/src/services/aks/tmp/_output/bin/aks /app/aks

RUN addgroup -S infrabox && adduser -S -G infrabox infrabox
USER infrabox

ENTRYPOINT ./aks
