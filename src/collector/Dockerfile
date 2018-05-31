FROM debian:9.4-slim

RUN apt-get update -y && apt-get install -y python  python-pip python-flask && \
    pip install flask_restplus eventlet && \
    apt-get remove -y python-pip && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/

COPY src/collector /collector
COPY src/pyinfraboxutils /pyinfraboxutils
COPY src/pyinfrabox /pyinfrabox

CMD python /collector/server.py
