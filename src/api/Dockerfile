FROM debian:9.3

RUN apt-get update -y && apt-get install -y python python-psycopg2 python-pip python-flask python-ldap && \
    pip install requests==2.18.4 PyJWT jsonschema cryptography flask_restplus eventlet flask_socketio boto3 google-cloud-storage future bcrypt \
    azure-mgmt-resource azure-storage && \
    apt-get remove -y python-pip && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/

COPY src/api /api
COPY src/pyinfraboxutils /pyinfraboxutils
COPY src/pyinfrabox /pyinfrabox

CMD python /api/server.py
