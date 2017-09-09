FROM stege/baseimage-gcloud:1

RUN apk update && apk add --no-cache py-pip && \
    pip install future minio && \
    apk del py-pip

COPY src/pyinfrabox/ /pyinfrabox
COPY src/job-api/server.py /server.py
COPY src/job-api/entrypoint.sh /entrypoint.sh
COPY src/utils/wait-for-postgres.sh /wait-for-postgres.sh

ENV PYTHONPATH=/pyinfrabox

RUN adduser -S apiuser
USER apiuser

CMD /entrypoint.sh
