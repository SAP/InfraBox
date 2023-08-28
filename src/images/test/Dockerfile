ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

# restore root user so we can have correct install path
USER root

COPY src/images/test/requirements_test.txt /infrabox/
RUN python -m pip install --no-cache-dir -r /infrabox/requirements_test.txt

USER infrabox
