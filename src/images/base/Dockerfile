# buster (10) is the last version to support Python 2.
# bullseye (11) although does have a Python 2 interpreter, 
# almost *all* Python 2 packages, however, have been removed from bullseye
# and bookworm (12) does not ship Python 2 at all
FROM debian:buster-slim

# gcc and python3-dev are necessary to build some wheels
# netbase offer /etc/protocols which is used by `getprotobyname` syscall
RUN apt-get update -y \
    && apt-get install --no-install-recommends -y \
        gcc \
        python3-dev \
        netbase \
        curl \
	    libpq-dev \
        python3 \
        python3-pip \
        python3-ldap \
        libxml2-dev \
        libxmlsec1-dev \
        openssh-client \
        inotify-tools \
    && apt-get autoremove -y \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

COPY src/images/base/requirements.txt /infrabox/

RUN python -m pip install -U pip && python -m pip -V && python -m pip install --no-cache-dir -r /infrabox/requirements.txt

RUN useradd -ms /bin/bash infrabox

USER infrabox
