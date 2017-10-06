FROM alpine:3.6

RUN apk update && apk add --no-cache python py-bottle py-psycopg2

COPY src/docker-registry/auth/server.py /server.py
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

RUN adduser -S auth
USER auth

CMD python /server.py
