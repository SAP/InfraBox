#!/bin/bash -e

docker_registry=${1:-""}
image_tag=${2:-"latest"}

echo "Building images for "
echo "  registry: $docker_registry"
echo "  tag: $image_tag"

infrabox run deploy/gerrit-api       -t ${docker_registry}infrabox/gerrit-api:$image_tag
infrabox run deploy/gerrit-trigger   -t ${docker_registry}infrabox/gerrit-trigger:$image_tag
infrabox run deploy/gerrit-review    -t ${docker_registry}infrabox/gerrit-review:$image_tag
infrabox run deploy/github-api       -t ${docker_registry}infrabox/github-api:$image_tag
infrabox run deploy/github-trigger   -t ${docker_registry}infrabox/github-trigger:$image_tag
infrabox run deploy/github-review    -t ${docker_registry}infrabox/github-review:$image_tag
infrabox run deploy/job              -t ${docker_registry}infrabox/job:$image_tag
infrabox run deploy/job-api          -t ${docker_registry}infrabox/job-api:$image_tag
infrabox run deploy/scheduler-kubernetes -t ${docker_registry}infrabox/scheduler-kubernetes:$image_tag
infrabox run deploy/scheduler-docker-compose -t ${docker_registry}infrabox/scheduler-docker-compose:$image_tag
infrabox run deploy/api              -t ${docker_registry}infrabox/api:$image_tag
infrabox run deploy/docs             -t ${docker_registry}infrabox/docs:$image_tag
infrabox run deploy/dashboard        -t ${docker_registry}infrabox/dashboard:$image_tag
infrabox run deploy/docker-auth      -t ${docker_registry}infrabox/docker-registry-auth:$image_tag
infrabox run deploy/docker-nginx     -t ${docker_registry}infrabox/docker-registry-nginx:$image_tag
infrabox run deploy/stats            -t ${docker_registry}infrabox/stats:$image_tag
infrabox run deploy/db               -t ${docker_registry}infrabox/db:$image_tag
infrabox run deploy/docker-gc        -t ${docker_registry}infrabox/docker-gc:$image_tag
