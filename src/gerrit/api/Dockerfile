from debian:8.9

RUN apt-get update -y && \
    apt-get install -y python-paramiko openssh-client python-requests python-bottle && \
    rm -rf /var/lib/apt/lists/*

ADD src/gerrit/api/api.py /api.py
ADD src/gerrit/api/entrypoint.sh /entrypoint.sh

CMD /entrypoint.sh
