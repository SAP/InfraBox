FROM docker:17.06

RUN apk add --no-cache python2 py2-requests py2-yaml py2-psycopg2 py2-jwt py2-cryptography

COPY src/scheduler/docker-compose scheduler
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

ENTRYPOINT python scheduler/scheduler.py
