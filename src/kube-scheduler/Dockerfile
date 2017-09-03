FROM alpine:3.4

RUN apk add --no-cache python py-psycopg2 py-requests py-pip && \
    pip install prometheus_client && \
    apk del py-pip

COPY src/kube-scheduler kube-scheduler

ENTRYPOINT ["python", "kube-scheduler/scheduler.py"]
