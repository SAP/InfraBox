ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-test:build_local

ENV PYTHONPATH=/infrabox/context/src

COPY infrabox/test/quotas /test
WORKDIR test

CMD /infrabox/context/infrabox/test/utils/python_tests.sh /infrabox/context/src/quotas '*'
