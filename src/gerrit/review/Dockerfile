ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

RUN apt-get update -y && \
    apt-get install -y python-paramiko openssh-client && \
    rm -rf /var/lib/apt/lists/*

COPY src/gerrit/review/review.py /review.py
COPY src/gerrit/review/entrypoint.sh /entrypoint.sh
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD /entrypoint.sh
