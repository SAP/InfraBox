#!/bin/bash -e
go build

export INFRABOX_GENERAL_DONT_CHECK_CERTIFICATES=true
export INFRABOX_LOCAL_CACHE_ENABLED=false
export INFRABOX_JOB_MAX_OUTPUT_SIZE=9999999
export INFRABOX_JOB_MOUNT_DOCKER_SOCKET=false
export INFRABOX_JOB_DAEMON_JSON='{}'
export INFRABOX_ROOT_URL="http://localhost:8080"
export INFRABOX_TAG=latest
export INFRABOX_DOCKER_REGISTRY="quay.io/infrabox"
export INFRABOX_LOCAL_CACHE_HOST_PATH=""
export INFRABOX_GERRIT_ENABLED=false

./job-controller -kubeconfig ~/.kube/config -logtostderr
