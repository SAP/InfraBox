FROM golang:1.10-alpine AS build-env

RUN apk add --no-cache git bash curl
RUN curl https://glide.sh/get | sh

COPY . /go/src/github.com/infrabox/infrabox/

WORKDIR /go/src/github.com/infrabox/infrabox/src/services/gke-cluster-controller

RUN glide install
RUN ./hack/update-codegen.sh
RUN go build

FROM alpine:3.6
WORKDIR /app
COPY --from=build-env /go/src/github.com/infrabox/infrabox/src/services/gke-cluster-controller/gke-cluster-controller /app/gke-cluster-controller

ENTRYPOINT ./gke-cluster-controller -logtostderr
