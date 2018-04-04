FROM postgres:9.5.5-alpine

COPY src/db/migrations/ /docker-entrypoint-initdb.d/

USER postgres
