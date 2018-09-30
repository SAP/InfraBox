FROM debian:9.5-slim

RUN    apt-get update -y \
    && apt-get install -y \
        python \
        python-pip \
        python-six \
        python-cryptography \
        python-crypto \
        python-pyasn1 \
    && pip install \
        psycopg2 \
        flask \
        flask_restplus==0.11.0 \
        flask_socketio \
        ldap \
        requests==2.18.4 \
        PyJWT \
        jsonschema \
        eventlet \
        boto3 \
        google-cloud-storage \
        future \
        bcrypt \
        pycrypto \
        azure-mgmt-resource \
        azure-storage \
        keystoneauth1==3.7.0 \
        python-swiftclient \
        bottle \
        python-cachetclient \
    && apt-get remove -y python-pip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*