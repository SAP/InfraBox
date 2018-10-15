import os
import certifi

ca_bundle = '/var/run/secrets/infrabox.net/certs/ca_bundle.pem'
if os.path.exists(ca_bundle):
    cafile = certifi.where()
    with open(ca_bundle, 'rb') as infile:
        customca = infile.read()

    with open(cafile, 'ab') as outfile:
        outfile.write(customca)
