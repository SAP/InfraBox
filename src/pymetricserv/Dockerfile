FROM python:3

RUN pip install psycopg2 && pip install prometheus_client

COPY src/pymetricserv/ pymetricserv/
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD /pymetricserv/pyserv.py

