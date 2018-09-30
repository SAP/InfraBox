ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-test:build_$INFRABOX_BUILD_NUMBER

ENV PYTHONPATH=/

COPY infrabox/test-registry/ /test/
COPY infrabox/test/utils/id_rsa /var/run/secrets/infrabox.net/rsa/id_rsa
COPY src/utils/wait-for-webserver.sh /wait-for-webserver.sh
COPY src/pyinfraboxutils /pyinfraboxutils

