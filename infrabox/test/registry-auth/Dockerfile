FROM alpine:3.6

RUN apk add --no-cache python py2-psycopg2 py2-pip gcc openssl libffi-dev python2-dev musl-dev py2-flask git openssl-dev && \
    pip install bcrypt PyJWT jsonschema coverage xmlrunner cryptography && \
    apk del gcc python2-dev musl-dev openssl-dev libffi-dev git

ENV PYTHONPATH=/

COPY src/docker-registry/auth /auth
COPY src/pyinfraboxutils /pyinfraboxutils
COPY infrabox/test/registry-auth /tests
COPY infrabox/test/utils/id_rsa /var/run/secrets/infrabox.net/rsa/id_rsa
COPY infrabox/test/utils/id_rsa.pub /var/run/secrets/infrabox.net/rsa/id_rsa.pub
COPY infrabox/test/utils/python_tests.sh /tests/entrypoint.sh

CMD /tests/entrypoint.sh /auth
