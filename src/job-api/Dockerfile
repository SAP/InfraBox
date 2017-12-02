FROM alpine:3.6

RUN apk add --no-cache \
    py2-pip \
    py2-cryptography \
    py2-jwt \
    py2-future \
    py2-psycopg2 \
    py2-flask \
    py2-pip && \
    pip install minio && \
    apk del py2-pip

COPY src/pyinfrabox/ /pyinfrabox
COPY src/job-api/server.py /server.py
COPY src/job-api/entrypoint.sh /entrypoint.sh
COPY src/utils/wait-for-postgres.sh /wait-for-postgres.sh
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/pyinfrabox:/

RUN adduser -S apiuser
USER apiuser

CMD /entrypoint.sh
