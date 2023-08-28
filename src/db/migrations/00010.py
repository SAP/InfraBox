import os

import base64

from Crypto.PublicKey import RSA
import psycopg2

public_key_path = os.environ.get('INFRABOX_RSA_PUBLIC_KEY_PATH', '/var/run/secrets/infrabox.net/rsa/id_rsa.pub')

# FIXME: pycryptodome 3.0 removes RSA ojbect `encrypt` method
def encrypt_secret(s):
    with open(public_key_path) as f:
        key = RSA.importKey(f.read())
        value = key.encrypt(str(s), 0)[0]
        return base64.b64encode(value)

def migrate(conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''
        SELECT id, value
        FROM secret
    ''')
    secrets = cur.fetchall()
    cur.close()

    for s in secrets:
        new_value = encrypt_secret(s['value'])

        cur = conn.cursor()
        cur.execute('''
            UPDATE secret
            SET value = %s
            WHERE id = %s
        ''', [new_value, s['id']])
        cur.close()
