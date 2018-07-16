FROM python:3

RUN pip install psycopg2 prometheus_client

COPY src/metrics/ metrics/
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD /metrics/server.py
