ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-test:build_$INFRABOX_BUILD_NUMBER

ENV PYTHONPATH=/infrabox/context/src

WORKDIR /infrabox/context/src/pyinfraboxutils

CMD ../../infrabox/test/utils/python_tests.sh /infrabox/context/src/pyinfraboxutils 'tests/*'