FROM alpine:3.6

RUN apk add --no-cache python py-psycopg2 py-requests py-pip && \
    pip install prometheus_client PyJWT && \
    apk del py-pip

COPY src/scheduler/kubernetes scheduler
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

ENTRYPOINT ["python", "scheduler/scheduler.py"]
