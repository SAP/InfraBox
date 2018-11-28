FROM golang:1.10-alpine AS build-env

RUN apk add --no-cache git curl bash
RUN curl https://raw.githubusercontent.com/golang/dep/master/install.sh | sh

COPY . /go/src/github.com/sap/infrabox/

WORKDIR /go/src/github.com/sap/infrabox/src/services/namespace

RUN dep ensure
RUN ./tmp/build/build.sh

FROM alpine:3.7

WORKDIR /app
COPY --from=build-env /go/src/github.com/sap/infrabox/src/services/namespace/tmp/_output/bin/namespace /app/namespace

RUN addgroup -S infrabox && adduser -S -G infrabox infrabox
USER infrabox

ENTRYPOINT ./namespace
