FROM debian:9.4-slim

RUN apt-get update -y && apt-get install -y python python-psycopg2 python-pip python-flask python-ldap && \
    pip install requests==2.18.4 PyJWT jsonschema cryptography flask_restplus eventlet flask_socketio boto3 google-cloud-storage future bcrypt pycrypto \
    azure-mgmt-resource azure-storage keystoneauth1 python-swiftclient && \
    apt-get remove -y python-pip && \
    rm -rf /var/lib/apt/lists/*

COPY src/checker checker
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

ENTRYPOINT ["python", "checker/checker.py"]
