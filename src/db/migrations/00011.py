import os

import base64

from Crypto.PublicKey import RSA

from pyinfraboxutils.secrets import encrypt_secret

import psycopg2

private_key_path = os.environ.get('INFRABOX_RSA_PRIVATE_KEY_PATH', '/var/run/secrets/infrabox.net/rsa/id_rsa')

def decrypt_secret(s):
    with open(private_key_path) as f:
        key = RSA.importKey(f.read())
        s = base64.b64decode(s)
        return key.decrypt(s)

def migrate(conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''
        SELECT id, value
        FROM secret
    ''')
    secrets = cur.fetchall()
    cur.close()

    for s in secrets:
        value = decrypt_secret(s['value'])
        new_value = encrypt_secret(value)

        cur = conn.cursor()
        cur.execute('''
            UPDATE secret
            SET value = %s
            WHERE id = %s
        ''', [new_value, s['id']])
        cur.close()
