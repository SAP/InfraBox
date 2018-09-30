ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-test:build_$INFRABOX_BUILD_NUMBER

ENV PYTHONPATH=/infrabox/context/src:/infrabox/context/src/docker-registry

COPY infrabox/test/utils/id_rsa /var/run/secrets/infrabox.net/rsa/id_rsa
COPY infrabox/test/utils/id_rsa.pub /var/run/secrets/infrabox.net/rsa/id_rsa.pub

WORKDIR /infrabox/context/infrabox/test/registry-auth

CMD ../utils/python_tests.sh /infrabox/context/src/docker-registry/auth
