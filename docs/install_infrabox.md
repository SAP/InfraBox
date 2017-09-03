# Install InfraBox

## Create secrets

    kubectl -n infrabox-system create secret generic \
        infrabox-dashboard \
        --from-literal=secret=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

## Install InfraBox
TODO
