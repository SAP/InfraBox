#!/bin/sh -e

ssh-keygen -N '' -t rsa -f id_rsa
ssh-keygen -f id_rsa.pub -e -m pem > id_rsa.pem

mkdir -p /infrabox/context/.infrabox/inputs/gen-compose

python /infrabox/context/deploy/install.py \
    --platform docker-compose \
    -o /infrabox/context/.infrabox/inputs/gen-compose/e2e \
    --general-rsa-public-key ./id_rsa.pem \
    --general-rsa-private-key ./id_rsa \
    --version build_184

cp -r /infrabox/context/.infrabox/inputs/gen-compose/e2e /infrabox/output/

python /infrabox/context/infrabox/test/gen-compose/patch.py
