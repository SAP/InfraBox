# buster (10) is the last version to support Python 2.
# bullseye (11) although does have a Python 2 interpreter, 
# almost *all* Python 2 packages, however, have been removed from bullseye
# and bookworm (12) does not ship Python 2 at all
FROM debian:buster-slim

COPY src/images/base/requirements.txt /infrabox/

RUN apt-get update -y \
    && apt-get install -y \
	    libpq-dev \
        python \
        python-pip \
        python-six \
        python-cryptography \
        python-crypto \
        python-pyasn1 \
        python-ldap \
        libxml2-dev \
        libxmlsec1-dev \
        python-paramiko \
        openssh-client \
        inotify-tools \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /infrabox/requirements.txt

RUN useradd -ms /bin/bash infrabox

USER infrabox
