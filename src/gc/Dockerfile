FROM alpine:3.7

RUN apk add --no-cache python3 py3-psycopg2 ca-certificates && \

COPY src/gc gc
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

ENTRYPOINT ["python3", "gc/gc.py"]
