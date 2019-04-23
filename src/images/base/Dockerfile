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
        psycopg2 \
        flask \
        flask_restplus \
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
        azure-storage \
        keystoneauth1==3.7.0 \
        python-swiftclient \
        python-cachetclient \
        python-saml \
        croniter \
    && apt-get remove -y python-pip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash infrabox
USER infrabox
