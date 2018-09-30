FROM debian:9.4-slim

RUN apt-get update -y && apt-get install -y python python-psycopg2 python-pip && \
    pip install python-cachetclient && \
    apt-get remove -y python-pip && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY src/status/cachet/cachet.py /cachet.py
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python /cachet.py
