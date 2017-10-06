FROM alpine:3.6

RUN apk add --no-cache python py-psycopg2 py-requests

COPY src/db db
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python db/migrate.py
