FROM quay.io/coreos/clair:v1.2.6
COPY src/clair/updater/config.yaml.template /config.yaml.template
COPY src/clair/updater/entrypoint.sh /entrypoint.sh
ENTRYPOINT /entrypoint.sh
