FROM debian:9.4-slim

RUN apt-get update -y && apt-get install -y python python-psycopg2 python-pip python-flask && \
    pip install bcrypt PyJWT jsonschema coverage xmlrunner cryptography codecov eventlet && \
    apt-get remove -y python-pip && \
    apt-get autoremove -y && \
	rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/infrabox/context/src:/infrabox/context/src/docker-registry

COPY infrabox/test/utils/id_rsa /var/run/secrets/infrabox.net/rsa/id_rsa
COPY infrabox/test/utils/id_rsa.pub /var/run/secrets/infrabox.net/rsa/id_rsa.pub

WORKDIR /infrabox/context/infrabox/test/registry-auth

CMD ../utils/python_tests.sh /infrabox/context/src/docker-registry/auth
