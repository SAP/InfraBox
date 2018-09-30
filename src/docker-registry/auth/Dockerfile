FROM debian:9.4-slim

RUN apt-get update -y && apt-get install -y python python-psycopg2 python-pip python-flask && \
    pip install eventlet PyJWT && \
    apt-get remove -y python-pip && \
    apt-get autoremove -y && \
	rm -rf /var/lib/apt/lists/*

COPY src/docker-registry/auth/server.py /server.py
COPY src/pyinfraboxutils /pyinfraboxutils
COPY src/pyinfrabox /pyinfrabox

ENV PYTHONPATH=/

CMD python /server.py
