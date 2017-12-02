FROM alpine:3.6

RUN apk add --no-cache \
    curl \
    py2-crypto \
    py2-requests \
    py2-psycopg2 \
    py-nose \
    py2-cryptography \
    py2-jwt

ENV PYTHONPATH=

COPY infrabox/test/job-api/test.py test.py
COPY infrabox/test/job-api/entrypoint.sh entrypoint.sh
COPY infrabox/test/utils/id_rsa /var/run/secrets/infrabox.net/rsa/id_rsa
COPY src/pyinfraboxutils /pyinfraboxutils
COPY src/utils/wait-for-webserver.sh wait-for-webserver.sh

CMD ["entrypoint.sh"]
