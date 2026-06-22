ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

ENV PYTHONPATH=/infrabox

COPY src/api /infrabox/api
COPY src/openpolicyagent /infrabox/openpolicyagent
COPY src/pyinfraboxutils /infrabox/pyinfraboxutils
COPY src/pyinfrabox /infrabox/pyinfrabox

RUN md5sum /infrabox/api/handlers/mcp/routes/jobs.py /infrabox/api/handlers/mcp/routes/builds.py

CMD python /infrabox/api/server.py
