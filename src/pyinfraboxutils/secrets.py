import os

import base64

from Crypto.PublicKey import RSA

private_key_path = os.environ.get('INFRABOX_RSA_PRIVATE_KEY_PATH', '/var/run/secrets/infrabox.net/rsa/id_rsa')
public_key_path = os.environ.get('INFRABOX_RSA_PUBLIC_KEY_PATH', '/var/run/secrets/infrabox.net/rsa/id_rsa.pub')

def encrypt_secret(s):
    with open(public_key_path) as f:
        key = RSA.importKey(f.read())
        value = key.encrypt(str(s), 0)[0]
        return base64.b64encode(value)

def decrypt_secret(s):
    with open(private_key_path) as f:
        key = RSA.importKey(f.read())
        s = base64.b64decode(s)
        return key.decrypt(s)
