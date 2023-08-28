ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-test:build_$INFRABOX_BUILD_NUMBER

ENV PYTHONPATH=/infrabox/context/src

COPY infrabox/test/utils/id_rsa /var/run/secrets/infrabox.net/rsa/id_rsa
COPY infrabox/test/utils/id_rsa.pub /var/run/secrets/infrabox.net/rsa/id_rsa.pub

COPY --chown=infrabox infrabox/test/pyinfraboxutils /test
WORKDIR /test

CMD /infrabox/context/infrabox/test/utils/python_tests.sh /infrabox/context/src/pyinfraboxutils '*'
