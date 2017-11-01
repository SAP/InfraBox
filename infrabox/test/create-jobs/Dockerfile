FROM alpine:3.6

RUN apk add --no-cache py2-pip py2-psycopg2 py-nose py2-yaml py2-jsonschema py2-crypto \
    postgresql-client py2-requests git curl
RUN pip install future docker PyJWT

RUN git config --global user.email "you@example.com"
RUN git config --global user.name "Your Name"
ENV PYTHONPATH=/project/src/job:/project/src
RUN mkdir /repo

COPY . /project
