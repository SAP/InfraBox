# Multi Cluster Setup
InfraBox can be installed on multiple Kubernetes cluster and connected to one big installation. See our blog post on why this can be useful for.

The multi cluster installation works almost as the regular installation, but with two additional requirements. The Postgres database you use has to be accessible by all clusters. So depending on your network and if you are on a cloud or on-prem you have to make the database available to all kubernetes installation with propper firewall rules.

The API Endpoints, bascially the `host` of each cluster must be accessible by all other clusters. If this is not possible for you, because you i.e. run one cluster on-prem and one in the cloud and you are not allowed to change your on-prem firewall rules to make the on-prem cluster accessible then see the [limitation section](limitation-if-not-all-clusters-are-accessible).

A Multi Cluster Setup always has one "master" installation. This one will contain the Dashboard and UI relevant components. The "worker" clusters will only host the API, Docker-Registry and Scheduler. You may also use different Storage backends on each cluster. So i.e. you want to run a master on AWS and a worker on GCP. So you would choose S3 on AWS and GCS on GCP, but remember the Postgres database must be available from all clusters so you could use Amazons' RDS or GCP's Cloud SQL.

You start with the regular instllation of the master, which could look like this (left out some configuration options to simplicity, see the instllation guide for a full list of require options):

```yaml
host: master.aws.my-domain.com
database:
  postgres:
    enabled: true
    db: infrabox
    host: my-db-host.my-domain.com
    password: myuser
    username: mypw
storage:
  s3:
    enabled: true
    access_key_id: myaccesskeyid
    bucket: infrabox
    secret_access_key: mysecretsaccesskey
```

With this you will get a full InfraBox installation on accessible at `https://master.aws.my-domain.com`. To add a worker simply copy the configuration of your master and sligthly change it:

```yaml
cluster:
  name: worker
  labels: my-worker,GCP
host: master.aws.my-domain.com
database:
  postgres:
    enabled: true
    db: infrabox
    host: my-db-host.my-domain.com
    password: myuser
    username: mypw
storage:
  gcs:
    enabled: true
    bucket: mybucket
    service_account: <base64 encoded service account .json>

```

A few things have to be changed:
- Every worker cluster requires its own `host`, which has to be accessible by all other clusters.
- `cluster.name` has to be set for each worker. This is a unique name to identify your cluster.
- `cluster.labels` is a comma separated list of labels. You may use the labels in your job definition to force a job to be executed on a cluster matching the labels.
- Storage configuration can be different but doesn't have to be. Prefer the storage local your installation. So if you ware on a cloud use the cloud's native storage option.

That's it. InfraBox should start up and automatically register itself as a worker cluster. Now you should be able to use the cluster selector in your job definition to force a job to be executed on a certain cluster:

    {
        "version": 1,
        "jobs": [{
            "name": "my-job",
            ...
            "cluster": {
                "selector": ["GCP"]
            }
        }]
    }

This job will now only be executed on clusters which have `GCP` in the `cluster.labels`. If you don't specify a `cluster.selector` the job may be executed on any cluster.

## Limitation if not all clusters are accessible
Sometimes it's not easily possible to make every cluster accessible to every other cluster. This is usually the case if you run on cluster inside your company network and another cluster on a cloud. Often you are not allowed to change your company's firewall rules to allow acces from outside of the network. In this case you can still use a multi cluster setup with some limitation.

The "master" installation (which contains the dashboard) must be accessible to all of your users, therefore this should run in your company network.

A InfraBox cluster needs access to another cluster mainly for two reasons:

1. A job running in cluster `A` produces some output in `/infrabox/output` and the child job is supposed to be run on cluster `B`. As each may use a different backend storage InfraBox will forward the output of the job from cluster `A` to cluster `B`. It uses the InfraBox API of each cluster (`host` of each cluster) to do this.
2. If you use `infrabox push` the source has to be uploaded to all clusters.

You can follow these rules to still use the multi cluster feature even if you cannot make every cluster accessible:

1. Install the "master" into a cluster which is accessible by all users (most probably your company network)
2. Use `cluster.selector` in your job definitions
3. A Parent job should always be run on a cluster which can access the child jobs cluster to be able to forward the output.



You can deploy multi cluster with [HA mode](/docs/ha_mode.md)
