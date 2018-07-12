FROM python:3

RUN pip install prometheus_client requests

COPY src/metrics/remote_target remote_target/


ENV PYTHONPATH=/

CMD /remote_target/server.py
