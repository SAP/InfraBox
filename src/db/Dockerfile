FROM debian:9.4-slim

RUN apt-get update -y && apt-get install -y python python-psycopg2 python-requests python-bcrypt python-crypto && \
    rm -rf /var/lib/apt/lists/*

COPY src/db db
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python db/migrate.py
