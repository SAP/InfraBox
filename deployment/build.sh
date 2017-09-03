#!/bin/bash -e

docker_registry=${1:-""}
image_tag=${2:-"latest"}

echo "Building images for "
echo "  registry: $docker_registry"
echo "  tag: $image_tag"

infrabox run -j deploy/api-server       -t ${docker_registry}infrabox/api-server:$image_tag
#infrabox run -j deploy/gerrit-review    -t ${docker_registry}infrabox/gerrit/review:$image_tag
#infrabox run -j deploy/gerrit-trigger   -t ${docker_registry}infrabox/gerrit/trigger:$image_tag
#infrabox run -j deploy/api              -t ${docker_registry}infrabox/api:$image_tag
#infrabox run -j deploy/job              -t ${docker_registry}infrabox/job:$image_tag
#infrabox run -j deploy/docs             -t ${docker_registry}infrabox/docs:$image_tag
infrabox run -j deploy/dashboard        -t ${docker_registry}infrabox/dashboard:$image_tag
#infrabox run -j deploy/kube-scheduler   -t ${docker_registry}infrabox/scheduler:$image_tag
#infrabox run -j deploy/clair-analyzer   -t ${docker_registry}infrabox/clair/analyzer:$image_tag
#infrabox run -j deploy/clair-updater    -t ${docker_registry}infrabox/clair/updater:$image_tag
#infrabox run -j deploy/docker-auth      -t ${docker_registry}infrabox/docker-registry/auth:$image_tag
#infrabox run -j deploy/docker-nginx     -t ${docker_registry}infrabox/docker-registry/nginx:$image_tag
#infrabox run -j deploy/postgres         -t ${docker_registry}infrabox/postgres:$image_tag
