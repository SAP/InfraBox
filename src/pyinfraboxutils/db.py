import time
import os
import psycopg2
import psycopg2.extras
from pyinfraboxutils import get_logger

logger = get_logger('infrabox')

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


class DB(object):
    def __init__(self, conn):
        self.conn = conn

    def execute_one(self, stmt, args=None):
        r = self.execute_many(stmt, args)
        if not r:
            return r

        return r[0]

    def execute_many(self, stmt, args=None):
        c = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute(stmt, args)
        r = c.fetchall()
        c.close()
        return r

    def execute_one_dict(self, stmt, args=None):
        r = self.execute_many_dict(stmt, args)
        if not r:
            return r

        return r[0]

    def execute_many_dict(self, stmt, args=None):
        c = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute(stmt, args)
        r = c.fetchall()
        c.close()
        return r

    def execute(self, stmt, args=None):
        c = self.conn.cursor()
        c.execute(stmt, args)
        c.close()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()
