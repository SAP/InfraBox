from debian:8.9

RUN apt-get update -y && \
    apt-get install -y python-psycopg2 python-paramiko openssh-client python-requests && \
    rm -rf /var/lib/apt/lists/*

COPY src/gerrit/trigger/trigger.py /trigger.py
COPY src/gerrit/trigger/entrypoint.sh /entrypoint.sh
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD /entrypoint.sh
