FROM alpine:3.6

RUN apk add --no-cache py2-flask py2-psycopg2 py2-jwt py2-cryptography py2-gevent

COPY src/docker-registry/auth/server.py /server.py
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

RUN adduser -S auth
USER auth

CMD python /server.py
