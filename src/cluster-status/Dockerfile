ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:$INFRABOX_BUILD_NUMBER

COPY src/cluster-status/server.py /server.py
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python /server.py
