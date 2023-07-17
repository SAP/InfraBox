import time
from datetime import datetime, timedelta

from pyinfraboxutils import get_logger, get_env
from pyinfraboxutils import dbpool
from pyinfraboxutils.storage import storage, SWIFT

logger = get_logger("gc")

class GC(object):
    def run(self):
        # TODO: Delete storage objects: uploads, outputs
        # TODO: Delete images from registry

        while True:
            db = dbpool.get()
            try:
                logger.info('Starting next GC run')
                self._gc(db)
                logger.info('Finished GC run')
                logger.info('')
            except Exception as e:
                logger.exception(e)
            finally:
                dbpool.put(db)

            time.sleep(3600)

    def _gc(self, db):
        self._gc_job_console_output(db)
        self._gc_job_output(db)
        self._gc_test_runs(db)
        self._gc_orphaned_projects(db)
        self._gc_storage_job_cache(db)
        self._gc_swift()

    def _gc_job_console_output(self, db):
        # Delete the console output of jobs
        # which are older than 30 days
        r = db.execute_one_dict('''
            SELECT count(*) as count
            FROM job
            WHERE created_at < NOW() - INTERVAL '30 days'
            AND console != 'deleted'
        ''')

        logger.info('Deleting console output of %s jobs', r['count'])

        r = db.execute('''
	        UPDATE job
            SET console = 'deleted'
            WHERE created_at < NOW() - INTERVAL '30 days'
            AND console != 'deleted'
        ''')

        db.commit()

    def _gc_test_runs(self, db):
        # Delete the test_runs
        # which are older than 30 days
        r = db.execute_one_dict('''
            SELECT count(*) as count
            FROM test_run
            WHERE timestamp < NOW() - INTERVAL '14 days'
        ''')

        logger.info('Deleting %s test_runs', r['count'])

        r = db.execute('''
            DELETE
            FROM test_run
            WHERE timestamp < NOW() - INTERVAL '14 days'
        ''')

        db.commit()


    def _gc_job_output(self, db):
        # Delete orphaned entries in the console table
        # which are older than one day
        r = db.execute_one_dict('''
            SELECT count(*) count
            FROM console
            WHERE date < NOW() - INTERVAL '1 day'
        ''')

        logger.info('Deleting %s orphaned console entries', r['count'])

        r = db.execute('''
            DELETE
            FROM console
            WHERE date < NOW() - INTERVAL '1 day'
        ''')

        db.commit()

    def _gc_orphaned_projects(self, db):
        # All the orphaned rows after a
        # project has been deleted
        tables = [
            'auth_token', 'build', 'collaborator', 'commit',
            'job', 'job_badge', 'job_markup', 'measurement',
            'pull_request', 'repository', 'secret', 'source_upload',
            'test_run'
        ]
        for t in tables:
            self._gc_table_content_of_deleted_project(db, t)

    def _gc_table_content_of_deleted_project(self, db, table):
        r = db.execute_one_dict('''
            SELECT count(*) as count
            FROM %s
            WHERE NOT EXISTS (
                SELECT project.id
                FROM project
                WHERE %s.project_id = project.id
            )
        ''' % (table, table))

        logger.info('Deleting %s orphaned rows from %s', r['count'], table)

        db.execute('''
            DELETE
            FROM %s
            WHERE NOT EXISTS (
                SELECT project.id
                FROM project
                WHERE %s.project_id = project.id
            )
        ''' % (table, table))

        db.commit()

    def _gc_storage_source_upload(self):
        pass

    def _gc_swift(self):
        if not isinstance(storage, SWIFT):
            return
        client = storage._get_client()
        for folder in ("archive/", "output/", "upload/", "segments/"):
            _, data = client.get_container(storage.container, prefix=folder, full_listing=True)
            now = datetime.now()
            for obj in data:
                # FIXME: when migrated to Python3, we can just use fromisoformat
                # last_modified = datetime.fromisoformat(obj["last_modified"])
                last_modified = datetime.strptime(obj["last_modified"], "%Y-%m-%dT%H:%M:%S.%f")
                if now - last_modified > timedelta(days=7):
                    storage._delete(obj["name"])
                    logger.info("deleted obj {}".format(obj['name']))

    def _gc_storage_job_cache(self, db):
        # Delete all cache of all jobs which have not
        # been executed in the last 7 days
        r = db.execute_many_dict('''
            SELECT DISTINCT project_id, name
            FROM job
            WHERE
            created_at > NOW() - INTERVAL '14 days'
            EXCEPT
            SELECT DISTINCT project_id, name from job where created_at > NOW() - INTERVAL '7 days'
        ''')

        logger.info('Deleting caches of %s jobs', len(r))

        for j in r:
            logger.info('Deleting cache %s/%s', j['project_id'], j['name'])
            key = 'project_%s_job_%s.tar.snappy' % (j['project_id'], j['name'])
            storage.delete_cache(key)

def main():
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')

    gc = GC()
    gc.run()

if __name__ == "__main__":
    main()
