FROM debian:9.6-slim

RUN    apt-get update -y \
    && apt-get install -y \
        libpq-dev \
        python3 \
        python3-pip \
        python3-six \
        python3-cryptography \
        python3-pyasn1 \
        python3-crypto \
        python-ldap \
        curl \
        git \
    && pip3 install \
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
        croniter \
    && apt-get remove -y python3-pip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash infrabox
USER infrabox
