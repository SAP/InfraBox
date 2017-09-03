FROM alpine:3.4

RUN apk add --no-cache \
    curl \
    python  \
    py-requests \
    py-psycopg2 \
    py-nose \
    py-flask \
    postgresql-client && \
    rm -rf /var/cache/apk/*
