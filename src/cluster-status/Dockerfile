ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

COPY src/cluster-status/server.py /server.py
COPY src/pyinfraboxutils /pyinfraboxutils
COPY src/pyinfrabox /pyinfrabox

ENV PYTHONPATH=/

CMD python /server.py
