FROM python:3

RUN pip install psycopg2 prometheus_client

COPY src/metrics/collector_server/ collector_server/
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD /collector_server/server.py
