FROM debian:9.5-slim

RUN    apt-get update -y \
    && apt-get install -y \
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
<<<<<<< HEAD
<<<<<<< HEAD
=======
        bottle \
>>>>>>> 2594bbc777c93c1aabba343774cdc3f150bafec6
=======
>>>>>>> 20455f7c39a05080fe7d22459cac779ea73394da
        python-cachetclient \
    && apt-get remove -y python-pip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
