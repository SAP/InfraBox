FROM alpine:3.6

RUN apk add --no-cache python3 py3-psycopg2 py3-requests py3-pip py3-cryptography && \
    pip3 install prometheus_client PyJWT && \
    apk del py3-pip

COPY src/scheduler/kubernetes scheduler
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

ENTRYPOINT ["python3", "scheduler/scheduler.py"]
