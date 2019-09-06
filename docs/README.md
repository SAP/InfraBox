# Documentation

## Install
- [Single Cluster installation](/docs/install/install.md)
- [Multi Cluster installation](/docs/install/multi_cluster.md)
- Services
    - [GCP Service](/src/services/gcp/README.md)
    - [AKS Service](/src/services/aks/README.md)
    - [Gardener Service](/src/services/gardener/README.md)

- [HA mode](/docs/install/ha_mode.md)

## Use InfraBox
- [Job definition](/docs/doc.md): How do define InfraBox jobs
- [Docker](/docs/job/docker.md): Build and Run a docker container
- [Docker Compose](/docs/job/docker_compose.md): Run multiple containers with docker-compose
- [Docker Image](/docs/job/docker_image.md): Run an already built image as job
- [Git](/docs/job/git.md): Include a git repository as sub workflow
- [Workflow](/docs/job/workflow.md): Split up your job definitions in multiple files
- [Cache Configuration](/docs/job/cache.md): Cache data and images
- [Environment Variables](/docs/job/env_vars.md): Set environment variables for your jobs
- [Secrets](/docs/job/secrets.md): Use secrets like passwords in your job
- [Resources](/docs/job/resources.md): Configure the resource limits of your job
- [Dependencies](/docs/job/dependencies.md): Define dependencies between jobs
- [Badges](/docs/job/badges.md): Create a custom badge
- [Repository](/docs/job/repository.md): Options to configure the git clone behavior
- [Deploy a docker image](/docs/job/deployments.md): Push a docker image to a registry
- [Private registry](/docs/job/source_registry.md): Pull images from a private registry
- [Private repositories](/docs/job/private_repo.md): Configure SSH Keys for accessing private repositories

## API Documentation
- [REST API](https://redocly.github.io/redoc/?url=https://infrabox.ninja/api/swagger.json)

## Extending InfraBox
- [Custom Services](/docs/services/custom_services.md)
