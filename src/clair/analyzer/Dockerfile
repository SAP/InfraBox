FROM quay.io/coreos/clair:v1.2.6
COPY src/clair/analyzer/config.yaml.template /config.yaml.template
COPY src/clair/analyzer/entrypoint.sh /entrypoint.sh
ENTRYPOINT /entrypoint.sh
