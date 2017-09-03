# Setup gerrit
To enable gerrit support set the configuration values

    gerrit.enabled = true
    gerrit.hostname = <YOUR_GERRIT_HOST>
    gerrit.port = <PORT>
    gerrit.username = <USERNAME_OF_THE_SSH_USER>

## Setup SSH
InfraBox needs access to gerrit with SSH. Create in infrabox-system and infrabox-worker namespace.

    kubectl -n <NAMESPACE> create secret generic \
        infrabox-gerrit-ssh \
        --from-file=id_rsa=[ID_RAS_FILE]


