FROM debian:9.3

RUN apt-get update -y && apt-get install -y python python-psycopg2 python-requests python-pip python-flask python-ldap && \
    pip install PyJWT jsonschema cryptography flask_restplus eventlet flask_socketio boto3 google-cloud-storage future bcrypt && \
    apt-get remove -y python-pip

ENV PYTHONPATH=/

COPY src/api /api
COPY src/pyinfraboxutils /pyinfraboxutils
COPY src/pyinfrabox /pyinfrabox

CMD python /api/server.py
