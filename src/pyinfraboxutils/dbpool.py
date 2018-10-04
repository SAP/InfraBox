import time
import os

import psycopg2

from eventlet.db_pool import ConnectionPool

from pyinfraboxutils.db import DB
from pyinfraboxutils import get_logger
logger = get_logger('dbpool')

POOL = ConnectionPool(psycopg2,
                      dbname=os.environ['INFRABOX_DATABASE_DB'],
                      user=os.environ['INFRABOX_DATABASE_USER'],
                      password=os.environ['INFRABOX_DATABASE_PASSWORD'],
                      host=os.environ['INFRABOX_DATABASE_HOST'],
                      port=os.environ['INFRABOX_DATABASE_PORT'],
                      min_size=0,
                      max_size=10)

def get():
    conn = POOL.get()
    return DB(conn)

def put(db):
    try:
        db.rollback()
    except Exception as e:
        logger.exception(e)

    POOL.put(db.conn)
    db.conn = None
