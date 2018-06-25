#!/usr/bin/env python
import sys
import threading
import time
from http.server import HTTPServer

import prometheus_client
import psycopg2
import random
import socket
from subprocess import run
from pyinfraboxutils import get_logger, get_env
from pyinfraboxutils.db import connect_db
from prometheus_client import Gauge, start_http_server, core


# A little python web server which collect datas overtime from the PostgreSQL Infrabox database

def execute_sql(conn, stmt, params):

    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute(stmt, params)
    result = c.fetchall()
    c.close()
    return result


class AllocatedRscGauge:
    def __init__(self, name):
        self._gauge = Gauge(name, "A gauge of allocated ressources of running jobs over time", ['cluster', 'rsc', 'project'])
        self._request_per_cluster = "SELECT foo.cluster_name, (SELECT name FROM project WHERE id= foo.project_id), " \
                                "foo.mem, foo.cpu FROM (SELECT cluster_name, project_id, sum(memory) as mem, " \
                                "sum(cpu) as cpu FROM job "\
                                "WHERE state='running' GROUP BY cluster_name, project_id) as foo"

        self._request_total = "SELECT (SELECT name FROM project WHERE id = foo.project_id), foo.mem, foo.cpu " \
                             "FROM (SELECT project_id, sum(memory) as mem, sum(cpu) as cpu "\
                                "FROM job "\
                                "WHERE state='running' GROUP BY project_id) as foo"

    def update(self, conn):
        per_cluster = execute_sql(conn, self._request_per_cluster, None)
        total = execute_sql(conn, self._request_total, None)
        self._set_values(per_cluster, total)

    def _set_values(self, per_cluster, total):
        for row in per_cluster:
            self._gauge.labels(rsc="mem", cluster=row[0], project=row[1]).set(row[2])
            self._gauge.labels(rsc="cpu", cluster=row[0], project=row[1]).set(row[3])

        for row in total:
            self._gauge.labels(rsc="mem", cluster="'%'", project=row[0]).set(row[1])
            self._gauge.labels(rsc="cpu", cluster="'%'", project=row[0]).set(row[2])

class JobGauge:
    def __init__(self, name):
        self._gauge = Gauge(name, "A histogram of current ammount of jobs",
                              ['state', 'cluster'])
        self._request_per_cluster = "SELECT cluster_name, count(id) filter(WHERE state = 'running'), " \
                                   "count(id) filter(WHERE state = 'queued'),count(id) filter(WHERE state = 'scheduled') " \
                                   "FROM job GROUP BY cluster_name"

        self._request_total = "SELECT count(id) filter(WHERE state = 'running'), " \
                             "count(id) filter(WHERE state = 'queued'), " \
                             "count(id) filter(WHERE state = 'scheduled') FROM job"

    def update(self, conn):
        per_cluster = execute_sql(conn, self._request_per_cluster, None)
        total = execute_sql(conn, self._request_total, None)
        self._set_values(per_cluster, total[0])

    def _set_values(self, per_cluster, total):
        for cluster_values in per_cluster:
            self._gauge.labels(state="running", cluster=cluster_values[0]).set(cluster_values[1])
            self._gauge.labels(state="queued", cluster=cluster_values[0]).set(cluster_values[2])
            self._gauge.labels(state="scheduled", cluster=cluster_values[0]).set(cluster_values[3])

        if total:
            self._gauge.labels(state="running", cluster="'%'").set(total[0])
            self._gauge.labels(state="queued", cluster="'%'").set(total[1])
            self._gauge.labels(state="scheduled", cluster="'%'").set(total[2])


def start_server(init_wait_time, threshold, port):
    """
    A little utility which try to launch the server, is used at least one time.
    Could be use in the future in the TRY main statement if http server stops unexceptedly
    :param init_wait_time:  Time to wait the first time, is incremented at each fail
    :param threshold:       When the wait time get to this value we stop trying
    :param port:            Port on which open the server
    """
    while init_wait_time <= threshold:
        try:
            start_http_server(int(port))
            return True
        except OSError:
            # TODO find the right log where to write it
            sys.stderr.write(
                "Unable to start the server on the {} port\nI'll wait {}s and try again".format(port, init_wait_time))
            time.sleep(init_wait_time)
            init_wait_time += 1
    return False

def main():
    # getting the env variables
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    server_port = get_env('PYMETRICSERV_PORT')

    # Copied from review.py, could be changed over time
    conn = connect_db()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    # When restarting or starting on a docker container, the port can be still used at the first try
    if not start_server(2, 5, server_port):
        return 1

    job_gauge = JobGauge('job_current_count')
    rsc_gauge = AllocatedRscGauge('rsc_current_count')

    while running:
        try:
            job_gauge.update(conn)
            rsc_gauge.update(conn)
        except psycopg2.OperationalError:
            # the db connection closed unexpectedly
            conn = connect_db()
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        # experimental value
        time.sleep(1.5)



if __name__ == '__main__':
    running = True
    main()





