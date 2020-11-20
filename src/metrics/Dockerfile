ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

COPY src/metrics/ metrics/
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python3 /metrics/server.py
