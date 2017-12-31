#!/bin/bash -e

docker_registry=${1:-""}
image_tag=${2:-"latest"}

echo "Pusing images for "
echo "  registry: $docker_registry"
echo "  tag: $image_tag"

docker push ${docker_registry}infrabox/gerrit-api:$image_tag
docker push ${docker_registry}infrabox/gerrit-trigger:$image_tag
docker push ${docker_registry}infrabox/gerrit-review:$image_tag
docker push ${docker_registry}infrabox/github-api:$image_tag
docker push ${docker_registry}infrabox/github-trigger:$image_tag
docker push ${docker_registry}infrabox/github-review:$image_tag
docker push ${docker_registry}infrabox/job:$image_tag
docker push ${docker_registry}infrabox/job-api:$image_tag
docker push ${docker_registry}infrabox/job-git:$image_tag
docker push ${docker_registry}infrabox/scheduler-kubernetes:$image_tag
docker push ${docker_registry}infrabox/scheduler-docker-compose:$image_tag
docker push ${docker_registry}infrabox/docker-compose-ingress:$image_tag
docker push ${docker_registry}infrabox/docker-compose-minio-init:$image_tag
docker push ${docker_registry}infrabox/api:$image_tag
docker push ${docker_registry}infrabox/dashboard-api:$image_tag
docker push ${docker_registry}infrabox/static:$image_tag
docker push ${docker_registry}infrabox/docker-registry-auth:$image_tag
docker push ${docker_registry}infrabox/docker-registry-nginx:$image_tag
docker push ${docker_registry}infrabox/stats:$image_tag
docker push ${docker_registry}infrabox/db:$image_tag
docker push ${docker_registry}infrabox/docker-gc:$image_tag
docker push ${docker_registry}infrabox/postgres:$image_tag
