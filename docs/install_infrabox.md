# Install InfraBox

## Create secrets

    kubectl -n infrabox-system create secret generic \
        infrabox-dashboard \
        --from-literal=secret=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

## Configure TLS
You may want to configure TLS for a more secure setup. It's highly recommended.

    dashboard.tls.enabled = true
    kubectl -n infrabox-system create secret generic \
            infrabox-dashboard-tls \
            --from-file=server.key=<KEY_FILE> \
            --from-file=server.crt=<CERT_FILE>

    dashboard.api.enabled = true
    kubectl -n infrabox-system create secret generic \
            infrabox-api-tls \
            --from-file=server.key=<KEY_FILE> \
            --from-file=server.crt=<CERT_FILE>

    dashboard.docs.enabled = true
    kubectl -n infrabox-system create secret generic \
            infrabox-docs-tls \
            --from-file=server.key=<KEY_FILE> \
            --from-file=server.crt=<CERT_FILE>

    dashboard.docker_registry.enabled = true
    kubectl -n infrabox-system create secret generic \
            infrabox-docker_registry-tls \
            --from-file=server.key=<KEY_FILE> \
            --from-file=server.crt=<CERT_FILE>

## Install InfraBox
TODO
