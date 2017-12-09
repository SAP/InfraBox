#!/bin/bash -e

docker_registry=${1:-""}
image_tag=${2:-"latest"}
cmd_prefix=${3:-"gcloud docker"}

echo "Pusing images for "
echo "  registry: $docker_registry"
echo "  tag: $image_tag"

$cmd_prefix -- push ${docker_registry}infrabox/job-api:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/gerrit-trigger:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/gerrit-review:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/gerrit-api:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/github-trigger:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/github-review:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/github-api:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/api:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/api-new:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/job:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/dashboard-api:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/scheduler-kubernetes:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/docker-registry-auth:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/docker-registry-nginx:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/stats:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/db:$image_tag
$cmd_prefix -- push ${docker_registry}infrabox/docker-gc:$image_tag
