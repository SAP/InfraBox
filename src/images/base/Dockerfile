FROM debian:9.6-slim

RUN    apt-get update -y \
    && apt-get install -y \
	libpq-dev \
        python3 \
        python3-pip \
        python3-six \
        python3-cryptography \
        python3-crypto \
        python3-pyasn1 \
        python-ldap \
        libxml2-dev \
        libxmlsec1-dev \
        python3-paramiko \
        openssh-client \
        inotify-tools \
    && pip3 install \
        psycopg2 \
        flask \
        flask-restx \
        flask_socketio \
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
        xmlsec \
        python3-saml \
        croniter \
    && apt-get remove -y python3-pip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash infrabox
USER infrabox
