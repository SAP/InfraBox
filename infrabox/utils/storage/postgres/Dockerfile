FROM postgres:9.5.5-alpine

COPY src/db/migrations/ /docker-entrypoint-initdb.d/
COPY infrabox/utils/storage/postgres/dummy_data/* /docker-entrypoint-initdb.d/

USER postgres
