FROM postgres:9.5.5-alpine

COPY src/postgres/schema_testing.sql /docker-entrypoint-initdb.d/

USER postgres
