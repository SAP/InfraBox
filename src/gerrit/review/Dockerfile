from debian:8.9

RUN apt-get update -y && \
    apt-get install -y python-psycopg2 python-paramiko openssh-client python-requests && \
    rm -rf /var/lib/apt/lists/*

ADD src/gerrit/review/review.py /review.py
ADD src/gerrit/review/entrypoint.sh /entrypoint.sh

CMD /entrypoint.sh
