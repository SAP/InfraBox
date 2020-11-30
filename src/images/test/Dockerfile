FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN    apt-get update -y \
    && apt-get install -y \
        pkg-config \
	    libpq-dev \
	    python3-dev \
        python3-pip \
        python3-cryptography \
        python3-pyasn1 \
        python3-crypto \
        libxml2-dev \
        libxmlsec1-dev \
        python3-paramiko \
        openssh-client \
        inotify-tools \
        libsasl2-dev \
        libldap2-dev \
        libssl-dev \
        libxmlsec1-openssl \
        curl \
        git \
    && pip3 install \
        six \
        python-ldap \
        psycopg2 \
        nose \
        pyyaml \
        coverage \
        unittest-xml-reporting \
        mock \
        codecov \
        flask \
        flask_restx \
        flask_socketio \
        requests==2.18.4 \
        PyJWT \
        jsonschema \
        eventlet \
        boto3 \
        google-cloud-storage \
        future \
        bcrypt \
        azure-mgmt-resource \
        azure-storage==0.36.0 \
        keystoneauth1==3.7.0 \
        python-swiftclient \
        python-cachetclient \
        croniter

RUN useradd -ms /bin/bash infrabox
USER infrabox
