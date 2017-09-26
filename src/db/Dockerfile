FROM alpine:3.6

RUN apk add --no-cache python py-psycopg2

COPY src/db db

CMD python db/migrate.py
