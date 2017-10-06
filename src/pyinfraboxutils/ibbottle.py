# pylint: disable=too-few-public-methods
import inspect
import os
from psycopg2.pool import SimpleConnectionPool
from bottle import HTTPResponse, HTTPError

class InfraBoxPostgresPlugin(object):
    name = 'ibpostgres'

    def __init__(self):
        self.pool = SimpleConnectionPool(1, 10,
                                         dbname=os.environ['INFRABOX_DATABASE_DB'],
                                         user=os.environ['INFRABOX_DATABASE_USER'],
                                         password=os.environ['INFRABOX_DATABASE_PASSWORD'],
                                         host=os.environ['INFRABOX_DATABASE_HOST'],
                                         port=os.environ['INFRABOX_DATABASE_PORT'])

    def apply(self, callback, context):
        # Test if the original callback accepts a 'conn' keyword.
        # Ignore it if it does not need a database connection.
        args = inspect.getargspec(context['callback'])[0]
        if 'conn' not in args:
            return callback

        def wrapper(*args, **kwargs):
            # Connect to the database
            conn = None
            try:
                conn = self.pool.getconn()
            except HTTPResponse, e:
                raise HTTPError(500, "Database Error", e)

            # Add the connection handle as a keyword argument.
            kwargs['conn'] = conn

            try:
                rv = callback(*args, **kwargs)
            except HTTPError, e:
                raise
            except HTTPResponse, e:
                raise
            finally:
                try:
                    conn.rollback()
                except:
                    pass
                self.pool.putconn(conn)
            return rv

        # Replace the route callback with the wrapped one.
        return wrapper

Plugin = InfraBoxPostgresPlugin
