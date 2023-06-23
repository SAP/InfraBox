# buster (10) is the last version to support Python 2.
# bullseye (11) although does have a Python 2 interpreter, 
# almost *all* Python 2 packages, however, have been removed from bullseye
# and bookworm (12) does not ship Python 2 at all
FROM debian:buster-slim

# make a symbol link to not break any python commands...
# currently we need gcc to build wheel for xmlsec (which is a dependency of python3-saml)
# so we cannot use --no-install-recommends to reduce image size

# version info:
# python3-pycryptodome: 3.6.1
RUN apt-get update -y \
    && apt-get install -y \
        curl \
	    libpq-dev \
        python3 \
        python3-pip \
        python3-pycryptodome \
        python3-ldap \
        libxml2-dev \
        libxmlsec1-dev \
        python3-paramiko \
        openssh-client \
        inotify-tools \
    && apt-get autoremove -y \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

COPY src/images/base/requirements.txt /infrabox/

RUN python -m pip install -U pip && python -m pip -V && python -m pip install --no-cache-dir -r /infrabox/requirements.txt

RUN useradd -ms /bin/bash infrabox

USER infrabox
