ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

RUN apt-get update -y && \
<<<<<<< HEAD
<<<<<<< HEAD
    apt-get install -y python-paramiko openssh-client && \
=======
    apt-get install -y python-paramiko openssh-client python-bottle && \
>>>>>>> 2594bbc777c93c1aabba343774cdc3f150bafec6
=======
    apt-get install -y python-paramiko openssh-client && \
>>>>>>> 20455f7c39a05080fe7d22459cac779ea73394da
    rm -rf /var/lib/apt/lists/*

COPY src/gerrit/api/api.py /api.py
COPY src/gerrit/api/entrypoint.sh /entrypoint.sh

CMD /entrypoint.sh
