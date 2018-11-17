ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

COPY src/github/trigger/trigger.py /trigger.py
COPY src/pyinfraboxutils /pyinfraboxutils
COPY src/pyinfrabox /pyinfrabox

ENV PYTHONPATH=/

CMD python /trigger.py
