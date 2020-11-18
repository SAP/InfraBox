ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-test:build_$INFRABOX_BUILD_NUMBER

ENV PYTHONPATH=/

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

COPY infrabox/test-registry/ /test/
COPY infrabox/test/utils/id_rsa /var/run/secrets/infrabox.net/rsa/id_rsa
COPY src/utils/wait-for-webserver.sh /wait-for-webserver.sh
COPY src/pyinfraboxutils /pyinfraboxutils

