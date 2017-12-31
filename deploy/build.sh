#!/bin/bash -e

docker_registry=${1:-""}
image_tag=${2:-"latest"}

echo "Building images for "
echo "  registry: $docker_registry"
echo "  tag: $image_tag"

infrabox run ib/deploy/gerrit-api       -t ${docker_registry}infrabox/gerrit-api:$image_tag
infrabox run ib/deploy/gerrit-trigger   -t ${docker_registry}infrabox/gerrit-trigger:$image_tag
infrabox run ib/deploy/gerrit-review    -t ${docker_registry}infrabox/gerrit-review:$image_tag
infrabox run ib/deploy/github-api       -t ${docker_registry}infrabox/github-api:$image_tag
infrabox run ib/deploy/github-trigger   -t ${docker_registry}infrabox/github-trigger:$image_tag
infrabox run ib/deploy/github-review    -t ${docker_registry}infrabox/github-review:$image_tag
infrabox run ib/deploy/job              -t ${docker_registry}infrabox/job:$image_tag
infrabox run ib/deploy/job-api          -t ${docker_registry}infrabox/job-api:$image_tag
infrabox run ib/deploy/job-git          -t ${docker_registry}infrabox/job-git:$image_tag
infrabox run ib/deploy/scheduler-kubernetes -t ${docker_registry}infrabox/scheduler-kubernetes:$image_tag
infrabox run ib/deploy/scheduler-docker-compose -t ${docker_registry}infrabox/scheduler-docker-compose:$image_tag
infrabox run ib/deploy/docker-compose-ingress -t ${docker_registry}infrabox/docker-compose-ingress:$image_tag
infrabox run ib/deploy/docker-compose-minio-init -t ${docker_registry}infrabox/docker-compose-minio-init:$image_tag
infrabox run ib/deploy/api              -t ${docker_registry}infrabox/api:$image_tag
infrabox run ib/deploy/dashboard-api    -t ${docker_registry}infrabox/dashboard-api:$image_tag
infrabox run ib/deploy/build-dashboard-client
infrabox run ib/deploy/static           -t ${docker_registry}infrabox/static:$image_tag
infrabox run ib/deploy/docker-auth      -t ${docker_registry}infrabox/docker-registry-auth:$image_tag
infrabox run ib/deploy/docker-nginx     -t ${docker_registry}infrabox/docker-registry-nginx:$image_tag
infrabox run ib/deploy/stats            -t ${docker_registry}infrabox/stats:$image_tag
infrabox run ib/deploy/db               -t ${docker_registry}infrabox/db:$image_tag
infrabox run ib/deploy/docker-gc        -t ${docker_registry}infrabox/docker-gc:$image_tag
infrabox run ib/deploy/postgres         -t ${docker_registry}infrabox/postgres:$image_tag
