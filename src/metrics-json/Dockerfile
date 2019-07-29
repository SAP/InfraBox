ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

COPY src/metrics-json/ metrics-json/
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python /metrics-json/server.py
