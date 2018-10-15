ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

COPY src/gc gc
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python gc/gc.py
