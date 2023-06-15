FROM debian:buster-slim

RUN    apt-get update -y \
    && apt-get install -y \
        libpq-dev \
        python \
        python-pip \
        python-six \
        python-cryptography \
        python-pyasn1 \
        python-crypto \
        python-ldap \
        curl \
        git \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY src/images/test/requirements_test_full.txt /infrabox/

RUN pip install --no-cache-dir -r /infrabox/requirements_test_full.txt

RUN useradd -ms /bin/bash infrabox

USER infrabox
