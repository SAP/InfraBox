import os

from pyinfraboxutils import get_logger, get_env, print_stackdriver
from pyinfraboxutils.db import connect_db
from pyinfraboxutils.leader import elect_leader

logger = get_logger("migrate")

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
        sql = sql_file.read().strip()

        cur = conn.cursor()
        if sql:
            cur.execute(sql)

        cur.execute('UPDATE infrabox SET schema_version = %s', (migration[1],))
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

    logger.info("Finished database migration")

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
    conn.close()

if __name__ == "__main__":
    try:
        main()
    except:
        print_stackdriver()
