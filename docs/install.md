# Minio

    $ cd deploy
    $ ./install_minio.sh

# Postgres
Replace REGISTRY and TAG accordingly:

    $ cd deploy/infrabox-postgres
    $ helm install -n infrabox-postgres --namespace infrabox-system --set docker_registry=<REGISTRY>,tag=<TAG> .

