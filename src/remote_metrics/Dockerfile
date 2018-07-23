FROM python:3

RUN pip install prometheus_client requests

COPY src/remote_metrics remote_metrics/


ENV PYTHONPATH=/

CMD /remote_metrics/server.py
