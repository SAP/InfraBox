ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

RUN apt-get update -y && \
<<<<<<< HEAD
    apt-get install -y python-paramiko openssh-client && \
=======
    apt-get install -y python-paramiko openssh-client python-bottle && \
>>>>>>> 2594bbc777c93c1aabba343774cdc3f150bafec6
    rm -rf /var/lib/apt/lists/*

COPY src/gerrit/review/review.py /review.py
COPY src/gerrit/review/entrypoint.sh /entrypoint.sh
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD /entrypoint.sh
