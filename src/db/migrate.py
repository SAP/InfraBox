import os
import re

import bcrypt
import importlib

from pyinfraboxutils import get_logger, get_env
from pyinfraboxutils.db import connect_db


# Matches C-style block comments (/* ... */), across multiple lines.
# Non-greedy so consecutive `/* a */ x /* b */` blocks are matched independently.
_BLOCK_COMMENT_RE = re.compile(r'/\*.*?\*/', re.DOTALL)

logger = get_logger("migrate")

def get_files(current_schema_version):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    migration_path = os.path.join(dir_path, 'migrations')

    files = [f for f in os.listdir(migration_path) if os.path.isfile(os.path.join(migration_path, f)) and f.startswith('0')]

    files.sort(key=lambda f: int(f[:5]))
    files = [f for f in files if int(f[:5]) > current_schema_version]

    return [(os.path.join(migration_path, f), int(f[:5])) for f in files]

def _has_executable_sql(sql):
    """Return True iff `sql` contains at least one non-comment, non-blank line.

    `str.strip()` only removes leading/trailing whitespace; SQL comments are
    kept.  Passing a comment-only string to `cur.execute()` raises
    `psycopg2.ProgrammingError: can't execute an empty query`, which breaks
    migration runs whenever a placeholder file (e.g. an intentionally empty
    migration to close a numbering gap) is applied.  This helper detects such
    files so the caller can skip the execute call.

    Recognised as "no SQL":
      - completely empty / whitespace-only files
      - only `-- ...` line comments
      - only `/* ... */` block comments (even across lines)
      - any combination of the above

    Lightweight heuristic — does not tokenise SQL, so quoted strings that
    happen to contain `--` or `/* */` are still treated as executable
    (which is fine, they contain real statements).
    """
    # Strip C-style block comments first so any `/* ... */`-only content is
    # collapsed away before the per-line `--` check.
    sql_no_block = _BLOCK_COMMENT_RE.sub('', sql)
    for line in sql_no_block.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith('--'):
            return True
    return False


def apply_migration(conn, migration):
    filename = migration[0]
    logger.info("Starting to apply migration %s", filename)

    if filename.endswith('.sql'):
        with open(migration[0]) as sql_file:
            sql = sql_file.read().strip()

            cur = conn.cursor()
            if _has_executable_sql(sql):
                cur.execute(sql)
            else:
                logger.info(
                    "Skipping execute for %s (no non-comment SQL statements)",
                    filename,
                )

            cur.close()
    elif filename.endswith('.py'):
        module_name = os.path.basename(filename)[:-3]
        m = importlib.import_module('migrations.%s' % module_name)
        m.migrate(conn)
    else:
        raise Exception('Unsupported migration file type: %s' % filename)

    cur = conn.cursor()
    cur.execute('UPDATE infrabox SET schema_version = %s', (migration[1],))
    cur.close()
    conn.commit()

def apply_migrations(conn, current_schema_version):
    migrations = get_files(current_schema_version)
    if not migrations:
        logger.info("No migration neccessary")
        return

    logger.info("Killing all open database connections")

    cur = conn.cursor()
    cur.execute('''
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = %s
          AND pid <> pg_backend_pid();
    ''', [get_env('INFRABOX_DATABASE_DB')])
    cur.close()
    conn.commit()

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

def configure_admin(conn):
    logger.info("Updating admin credentials")

    password = get_env('INFRABOX_ADMIN_PASSWORD')
    email = get_env('INFRABOX_ADMIN_EMAIL')

    hashed_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt()).decode()

    cur = conn.cursor()
    cur.execute('''
        INSERT into "user" (id, username, name, email, password, role)
        VALUES ('00000000-0000-0000-0000-000000000000', 'Admin', 'Admin', %s, %s, 'admin')
        ON CONFLICT (id) DO UPDATE
        SET email = %s,
            password = %s
    ''', [email, hashed_password, email, hashed_password])
    cur.close()
    conn.commit()

def main():
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_ADMIN_PASSWORD')
    get_env('INFRABOX_ADMIN_EMAIL')

    conn = connect_db()
    migrate_db(conn)
    configure_admin(conn)
    conn.close()

if __name__ == "__main__":
    main()
