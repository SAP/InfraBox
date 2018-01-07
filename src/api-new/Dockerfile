FROM alpine:3.6

RUN apk add --no-cache python py2-psycopg2 py2-pip gcc openssl libffi-dev python2-dev musl-dev py2-flask openssl-dev py2-requests && \
    pip install PyJWT jsonschema cryptography flask_restplus eventlet flask_socketio boto3 google-cloud-storage future && \
    apk del gcc python2-dev musl-dev openssl-dev libffi-dev

ENV PYTHONPATH=/

COPY src/api-new /api
COPY src/pyinfraboxutils /pyinfraboxutils
COPY src/pyinfrabox /pyinfrabox

CMD python /api/server.py
