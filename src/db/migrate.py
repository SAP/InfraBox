import logging
import time
import os
import json
import traceback
import psycopg2
import psycopg2.extensions
import requests

logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.INFO
)

logger = logging.getLogger("migrate")

def get_env(name):
    if name not in os.environ:
        raise Exception("%s not set" % name)
    return os.environ[name]

def connect_db():
    while True:
        try:
            conn = psycopg2.connect(dbname=os.environ['INFRABOX_DATABASE_DB'],
                                    user=os.environ['INFRABOX_DATABASE_USER'],
                                    password=os.environ['INFRABOX_DATABASE_PASSWORD'],
                                    host=os.environ['INFRABOX_DATABASE_HOST'],
                                    port=os.environ['INFRABOX_DATABASE_PORT'])
            return conn
        except Exception as e:
            logger.warn("Could not connect to db: %s", e)
            time.sleep(3)

def elect_leader():
    while True:
        r = requests.get("http://localhost:4040", timeout=5)
        leader = r.json()['name']

        if leader == os.environ['HOSTNAME']:
            logger.info("I'm the leader")
            break
        else:
            logger.info("I'm not the leader, %s is the leader", leader)
            time.sleep(1)

def get_sql_files(current_schema_version):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    migration_path = os.path.join(dir_path, 'migrations')

    files = [f for f in os.listdir(migration_path) if os.path.isfile(os.path.join(migration_path, f))]

    files.sort(key=lambda f: int(f[:-4]))
    files = files[current_schema_version:]

    return [(os.path.join(migration_path, f), int(f[:-4])) for f in files]

def apply_migration(conn, migration):
    logger.info("Starting to apply migration %s", migration[1])
    with open(migration[0]) as sql_file:
        sql = sql_file.read()
        cur = conn.cursor()
        cur.execute(sql)
        cur.execute('UPDATE infrabox SET schema_version = %s', migration[1])
        cur.close()
        conn.commit()

def apply_migrations(conn, current_schema_version):
    migrations = get_sql_files(current_schema_version)
    logger.info("Starting to apply %s migrations", len(migrations))

    for m in migrations:
        apply_migration(conn, m)


def migrate_db(conn):
    logger.info("Starting schema migration")
    current_schema_version = 0

    cur = conn.cursor()
    cur.execute('''
        SELECT *
        FROM information_schema.tables
        WHERE table_name = 'infrabox'
    ''')
    result = cur.fetchall()
    cur.close()

    if result:
        cur = conn.cursor()
        cur.execute('''
            SELECT schema_version
            FROM infrabox
        ''')
        result = cur.fetchone()
        cur.close()
        current_schema_version = result[0]
    else:
        logger.info("infrabox table does not exist")

    logger.info("Current schema version is: %s", current_schema_version)

    apply_migrations(conn, current_schema_version)

def main():
    get_env('INFRABOX_SERVICE')
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')

    elect_leader()
    conn = connect_db()
    migrate_db(conn)


def print_stackdriver():
    if 'INFRABOX_GENERAL_LOG_STACKDRIVER' in os.environ and os.environ['INFRABOX_GENERAL_LOG_STACKDRIVER'] == 'true':
        print json.dumps({
            "serviceContext": {
                "service": os.environ.get('INFRABOX_SERVICE', 'unknown'),
                "version": os.environ.get('INFRABOX_VERSION', 'unknown')
            },
            "message": traceback.format_exc(),
            "severity": 'ERROR'
        })
    else:
        print traceback.format_exc()

if __name__ == "__main__":
    try:
        main()
    except:
        print_stackdriver()
