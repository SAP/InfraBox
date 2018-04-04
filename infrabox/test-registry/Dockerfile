FROM alpine:3.6

RUN apk add --no-cache py2-flask py2-cryptography py2-jwt curl py-nose py2-psycopg2 py2-requests

ENV PYTHONPATH=/

COPY infrabox/test-registry/ /test/
COPY infrabox/test/utils/id_rsa /var/run/secrets/infrabox.net/rsa/id_rsa
COPY src/utils/wait-for-webserver.sh /wait-for-webserver.sh
COPY src/pyinfraboxutils /pyinfraboxutils

