# HA setup

Infrabox support ha mode when deployed multi clusters.

Related configuratios:
```yaml
ha:
    enabled: false

    check_interval: 10

    active_timeout: 60

    global_host: #<required if use ha>

    global_port: 443
```

## Enable HA mode
set `ha.enabled = true` to enable ha mode

HA mode makes every cluster accessable, we need to set a fixed entrypoint by setting`entry_host, entry_port` and create tls secret named `infrabox-ha-tls-certs`

Every cluster has its own root_url and can be accessed from both root_url and  global url `https://global_host:global_port`

In order to access InfraBox from global_url, tls certificate named infrabox-ha-tls-certs for global_url should be created
```bash
kubectl create -n infrabox-system secret tls infrabox-ha-tls-certs --key <PATH_TO_KEY>.key --cert <PATH_TO_CRT>.crt
```

## Configure HA mode

- When ha mode is enabled, Infrabox checks every cluster repeatedly. 
The checker checks these items:
    - pods status in namespace infrabos-system
    - dashboard connection
    - api connection
    - storage upload/download test
    
Check interval can be configured by `check_interval (seconds)`

- By default, a cluster not running for 60 seconds is considered inactive, jobs will not be scheduled to this cluster.
HA timeout time can be configurated by `ha.active_timeout`

- Jobs without cluster selector will be scheduled to clusters with `default` label, it's better to add label `default` to your clusters.

- In ha mode, we don't have a master cluster, so there is no need to set a cluster with name master


