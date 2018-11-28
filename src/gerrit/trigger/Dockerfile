ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

COPY src/gerrit/trigger/trigger.py /trigger.py
COPY src/gerrit/trigger/entrypoint.sh /entrypoint.sh
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD /entrypoint.sh
