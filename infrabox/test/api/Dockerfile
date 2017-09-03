FROM alpine:3.4

RUN apk add --no-cache python py-pip py-psycopg2 py-nose py-yaml \
    postgresql-client py-requests curl
RUN pip install jsonschema future docker

ADD infrabox/test/api /test

ADD src/utils /utils

