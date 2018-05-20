import os
import hashlib
import base64

from Crypto import Random
from Crypto.Cipher import AES

private_key_path = os.environ.get('INFRABOX_RSA_PRIVATE_KEY_PATH', '/var/run/secrets/infrabox.net/rsa/id_rsa')

class AESCipher(object):

    def __init__(self, key):
        self.bs = 32
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

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
