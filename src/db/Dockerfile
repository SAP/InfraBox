FROM debian:9.3

RUN apt-get update -y && apt-get install -y python python-psycopg2 python-requests python-bcrypt

COPY src/db db
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python db/migrate.py
