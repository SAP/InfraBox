FROM alpine:3.4

RUN apk add --no-cache python py-pip py-psycopg2 py-nose py-yaml \
    postgresql-client py-requests git curl
RUN pip install jsonschema future docker

RUN git config --global user.email "you@example.com"
RUN git config --global user.name "Your Name"
ENV PYTHONPATH=/project/src/job:/project/src
RUN mkdir /repo

COPY . /project
