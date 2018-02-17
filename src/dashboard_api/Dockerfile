FROM debian:9.3

RUN apt-get update -y && apt-get install -y python python-psycopg2 python-requests python-pip python-flask python-ldap && \
    pip install PyJWT jsonschema cryptography flask_restplus eventlet flask_socketio boto3 google-cloud-storage future prometheus_client bcrypt && \
    apt-get remove -y python-pip

ENV PYTHONPATH=/code

COPY src/dashboard_api /code/dashboard_api
COPY src/pyinfraboxutils /code/pyinfraboxutils
COPY src/pyinfrabox /code/pyinfrabox

CMD python /code/dashboard_api/__init__.py
