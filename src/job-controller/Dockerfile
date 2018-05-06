FROM golang:1.10-alpine AS build-env

RUN apk add --no-cache git bash
RUN go get github.com/tools/godep

COPY . /go/src/github.com/infrabox/infrabox/

WORKDIR /go/src/github.com/infrabox/infrabox/src/job-controller

RUN godep restore
RUN ./hack/update-codegen.sh
RUN go get
RUN go build

FROM alpine:3.6
WORKDIR /app
COPY --from=build-env /go/src/github.com/infrabox/infrabox/src/job-controller /app/job-controller

ENTRYPOINT ./job-controller/job-controller -logtostderr
