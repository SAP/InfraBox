import os
import hashlib
import base64

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

private_key_path = os.environ.get('INFRABOX_RSA_PRIVATE_KEY_PATH', '/var/run/secrets/infrabox.net/rsa/id_rsa')

class AESCipher:
    def __init__(self, key):
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = raw.encode()
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(pad(raw, self.bs))).decode()

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        ciphertext = enc[AES.block_size:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(ciphertext), self.bs).decode()

def encrypt_secret(s):
    with open(private_key_path) as f:
        key = f.read()
        a = AESCipher(key)
        return a.encrypt(str(s))

def decrypt_secret(s):
    with open(private_key_path) as f:
        key = f.read()
        a = AESCipher(key)
        return a.decrypt(str(s))
