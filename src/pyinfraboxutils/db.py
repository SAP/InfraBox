import time
import os
import psycopg2
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
