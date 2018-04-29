FROM debian:9.3-slim

RUN apt-get update -y && apt-get install -y python python-psycopg2 python-requests python-bcrypt python-crypto

COPY src/db db
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python db/migrate.py
