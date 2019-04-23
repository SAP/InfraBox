FROM debian:9.6-slim

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
    && pip install \
        psycopg2 \
        nose \
        pyyaml \
        coverage \
        xmlrunner \
        mock \
        codecov \
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
        azure-mgmt-resource \
        azure-storage \
        keystoneauth1==3.7.0 \
        python-swiftclient \
        python-cachetclient \
        croniter \
    && apt-get remove -y python-pip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash infrabox
USER infrabox
