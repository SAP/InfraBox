FROM alpine:3.6

RUN apk add --no-cache py2-flask py2-psycopg2 py2-jwt py2-cryptography py2-gevent
ENV PYTHONPATH=/

COPY src/docker-registry/auth/server.py /server.py
COPY src/pyinfraboxutils /pyinfraboxutils
COPY infrabox/test/utils/id_rsa.pub /var/run/secrets/infrabox.net/rsa/id_rsa.pub

CMD python /server.py
