FROM alpine:3.6

RUN apk add --no-cache python py-pip py-psycopg2 py-yaml \
    postgresql-client py-requests curl
RUN pip install jsonschema future docker xmlrunner

COPY infrabox/test/api /test

COPY src/utils /utils
