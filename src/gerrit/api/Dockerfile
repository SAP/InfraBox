ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

RUN apt-get update -y && \
    apt-get install -y python-paramiko openssh-client && \
    rm -rf /var/lib/apt/lists/*

COPY src/gerrit/api/api.py /api.py
COPY src/gerrit/api/entrypoint.sh /entrypoint.sh

CMD /entrypoint.sh
