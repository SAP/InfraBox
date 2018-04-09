FROM alpine:3.6

RUN apk add --no-cache python py2-psycopg2 py2-pip gcc openssl libffi-dev python2-dev musl-dev py2-flask git openssl-dev && \
    pip install bcrypt PyJWT jsonschema coverage xmlrunner cryptography codecov && \
    apk del gcc python2-dev musl-dev openssl-dev libffi-dev

ENV PYTHONPATH=/infrabox/context/src:/infrabox/context/src/docker-registry

COPY infrabox/test/utils/id_rsa /var/run/secrets/infrabox.net/rsa/id_rsa
COPY infrabox/test/utils/id_rsa.pub /var/run/secrets/infrabox.net/rsa/id_rsa.pub

WORKDIR /infrabox/context/infrabox/test/registry-auth

CMD ../utils/python_tests.sh /infrabox/context/src/docker-registry/auth
