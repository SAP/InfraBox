import psycopg2

from pyinfraboxutils.secrets import encrypt_secret

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
