FROM alpine:3.6

RUN apk add --no-cache py2-yaml py2-pip py-future git && \
    pip install coverage codecov xmlrunner

ENV PYTHONPATH=/infrabox/context/src

WORKDIR /infrabox/context/src/pyinfrabox

CMD ../../infrabox/test/utils/python_tests.sh /infrabox/context/src/pyinfrabox 'tests/*'
