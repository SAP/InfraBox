FROM debian:9.6-slim

RUN    apt-get update -y \
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
    && pip install \
        pyrsistent==0.15.7 \
        six==1.14.0 \
        psycopg2 \
        flask \
        flask-restx \
        flask_socketio==4.3.1 \
        requests==2.18.4 \
        PyJWT \
        jsonschema \
        eventlet \
        boto3 \
        google-cloud-storage \
        future \
        bcrypt \
        pycrypto \
        prometheus_client \
        azure-mgmt-resource \
        azure-storage==0.36.0 \
        keystoneauth1==3.7.0 \
        python-swiftclient \
        python-cachetclient \
        python-saml \
        python-engineio==3.13.2 \
        croniter \
    && apt-get remove -y python-pip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash infrabox

USER infrabox
