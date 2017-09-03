#!/bin/bash -e

docker_registry=${1:-""}
image_tag=${2:-"latest"}

echo "Pusing images for "
echo "  registry: $docker_registry"
echo "  tag: $image_tag"

docker push ${docker_registry}infrabox/api-server:$image_tag
docker push ${docker_registry}infrabox/gerrit/trigger:$image_tag
docker push ${docker_registry}infrabox/gerrit/review:$image_tag
docker push ${docker_registry}infrabox/api:$image_tag
docker push ${docker_registry}infrabox/docs:$image_tag
docker push ${docker_registry}infrabox/job:$image_tag
docker push ${docker_registry}infrabox/dashboard:$image_tag
docker push ${docker_registry}infrabox/scheduler:$image_tag
docker push ${docker_registry}infrabox/clair/analyzer:$image_tag
docker push ${docker_registry}infrabox/clair/updater:$image_tag
docker push ${docker_registry}infrabox/docker-registry/auth:$image_tag
docker push ${docker_registry}infrabox/docker-registry/nginx:$image_tag
docker push ${docker_registry}infrabox/postgres:$image_tag
