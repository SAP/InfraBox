#!/usr/bin/env python
import sys
import time
import os

import psycopg2
from pyinfraboxutils import get_env
from pyinfraboxutils.db import connect_db
from prometheus_client import Gauge, start_http_server


# A little python web server which collect datas overtime from the PostgreSQL Infrabox database

def execute_sql(conn, stmt, params):
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute(stmt, params)
    result = c.fetchall()
    c.close()
    return result


class AllocatedRscGauge:
    def __init__(self, name, conn):
        self._gauge = Gauge(name, "A gauge of allocated ressources of running jobs over time",
                            ['cluster', 'rsc', 'project'])
        self._request_per_cluster = '''
            SELECT foo.cluster_name,
                   (SELECT name FROM project WHERE id= foo.project_id),
                   foo.mem, foo.cpu
            FROM (
                    SELECT cluster_name, project_id, sum((definition#>>'{resources,limits,memory}')::integer) as mem,
                    sum((definition#>>'{resources,limits,cpu}')::decimal) as cpu FROM job
                    WHERE state='running'
                    GROUP BY cluster_name, project_id
                 ) as foo
        '''

        self._request_total = """
            SELECT (SELECT name FROM project WHERE id = foo.project_id), foo.mem, foo.cpu
            FROM (SELECT project_id,
                         sum((definition#>>'{resources,limits,memory}')::integer) as mem,
                         sum((definition#>>'{resources,limits,cpu}')::decimal) as cpu
                  FROM job
                  WHERE state='running'
                  GROUP BY project_id) as foo
        """

        self._request_possible_cluster = "SELECT DISTINCT name FROM cluster ORDER BY name"
        self._request_possible_projects = "SELECT DISTINCT name FROM project ORDER BY name"
        self._possible_combination = None
        self._possible_cluster = None
        self._possible_project = None
        self._count_to_update = 10
        self._create_combination_dict(conn)

    def _create_combination_dict(self, conn):
        """
        Completely rewrite the combination dict based on the occurrences of the request results without any
        data loss checks made on old cluster or project occurrences.
        """
        self._possible_cluster = execute_sql(conn, self._request_possible_cluster, None)
        self._possible_cluster.append(["'%'"])
        self._possible_project = execute_sql(conn, self._request_possible_projects, None)

        self._possible_combination = dict()
        for cluster in self._possible_cluster:
            if cluster[0]:
                project_dict = dict()
                for project in self._possible_project:
                    if project[0]:
                        project_dict[project[0]] = True
                self._possible_combination[cluster[0]] = project_dict

    def _update_combination_dict(self, conn):
        """
        Check if the dict must be updated with new values and updates it if necessary.
        To do so we overwrite old values as well as the new ones => check before.

        IT DOES NOT set old values to True (the existence test among list is not efficient),
        we still need to reset all the values by calling _reset_combination_dict
        """
        tmp_possible_cluster = execute_sql(conn, self._request_possible_cluster, None)
        tmp_possible_cluster.append(["'%'"])
        tmp_possible_project = execute_sql(conn, self._request_possible_projects, None)

        if AllocatedRscGauge._different_instance_list(self._possible_cluster, tmp_possible_cluster) or \
            AllocatedRscGauge._different_instance_list(self._possible_project, tmp_possible_project):
            print("=== DICT UPDATE - AVOIDABLE COST ===")
            for cluster in self._possible_cluster:
                if cluster[0]:
                    project_dict = self._possible_combination.get(cluster[0])
                    if not project_dict:
                        project_dict = dict()
                        self._possible_combination[cluster[0]] = project_dict
                    for project in self._possible_project:
                        if project[0]:
                            project_dict[project[0]] = True

    def _reset_combination_dict(self):
        """
        Set all the occurrences of the combination dict to True in order to detect which values to set to 0
        because they are missing in the request result
        """
        for project_dict in self._possible_combination.values():
            for project_name in project_dict.keys():
                project_dict[project_name] = True

    @staticmethod
    def _different_instance_list(first, second):
        """
        Return True if the given contains a difference in there occurrences.
        Used to detect if we should update the combination dictionary.
        Example : a new project or a new cluster appeared in the DB
        """
        length = len(first)
        if length != len(second):
            return True
        else:
            for i in range(length):
                if first[i][0] != second[i][0]:
                    return True
        return False

    def update(self, conn):
        per_cluster = execute_sql(conn, self._request_per_cluster, None)
        total = execute_sql(conn, self._request_total, None)
        if self._count_to_update == 0:
            self._update_combination_dict(conn)
            self._count_to_update = 10
        self._reset_combination_dict()
        self._set_values(per_cluster, total)
        self._count_to_update -= 1

    def _set_values(self, per_cluster, total):
        for row in per_cluster:
            project_dict = self._possible_combination.get(row[0])
            if project_dict and project_dict.get(row[1]):
                project_dict[row[1]] = False

            self._gauge.labels(rsc="mem", cluster=row[0], project=row[1]).set(row[2])
            self._gauge.labels(rsc="cpu", cluster=row[0], project=row[1]).set(row[3])

        for row in total:
            project_dict = self._possible_combination.get("'%'")
            if project_dict and project_dict.get(row[0]):
                project_dict[row[0]] = False

            self._gauge.labels(rsc="mem", cluster="'%'", project=row[0]).set(row[1])
            self._gauge.labels(rsc="cpu", cluster="'%'", project=row[0]).set(row[2])

        for cluster, project_dict in self._possible_combination.items():
            to_delete = []
            for project, not_used in project_dict.items():
                if not_used:
                    to_delete.append(project)
                    self._gauge.labels(rsc="mem", cluster=cluster, project=project).set(0)
                    self._gauge.labels(rsc="cpu", cluster=cluster, project=project).set(0)

            # Maybe it was the last occurrence ever of this datas. We delete it in order to keep the combination dict
            # as small as possible (would be running for entire weeks maybe)
            for maybe_last_occurrence in to_delete:
                del project_dict[maybe_last_occurrence]


class AllJobNodeGauge:
    def __init__(self, name):
        self._gauge = Gauge(name, "A gauge of current amount of all jobs",
                            ['state', 'node'])

        self._request_possible_states = "SELECT distinct state FROM job"

        self._request_possible_node = "SELECT distinct node_name FROM job"

        self._request_per_node = "SELECT node_name, state, count(id) " \
                                 "FROM job WHERE node_name is not null GROUP BY node_name, state"

        self._possible_combination = dict()
        self._count_to_reset_nodes = 0
        self._possible_nodes = None
        self._possibles_states = None

    def update(self, conn):
        self._reset_used_combination(conn)
        per_node = execute_sql(conn, self._request_per_node, None)
        self._set_values(per_node)

    def _reset_used_combination(self, conn):
        """
        Resetting the boolean dictionary in order to be able to detect which state to set to 0
        We could have managed this directly on PostGres but the cross to make to have all possible combinations
        of node / state was making the request really slow (> 500ms)
        """
        self._possible_combination = dict()

        if self._count_to_reset_nodes == 0:
            # The slowest part, we only update it every ~20 seconds, might cause a delay in graphs for null
            # counters when creating a new node or new state
            self._possible_nodes = execute_sql(conn, self._request_possible_node, None)
            self._possibles_states = execute_sql(conn, self._request_possible_states, None)
            self._count_to_reset_nodes = 10

        for node in self._possible_nodes:
            if not node[0]:
                continue
            possible_state = dict()
            for state in self._possibles_states:
                possible_state[state[0]] = True
            self._possible_combination[node[0]] = possible_state

    def _set_values(self, per_node):
        for row in per_node:
            node_dict = self._possible_combination.get(row[0])
            if node_dict and node_dict.get(row[1]) is not None:
                node_dict[row[1]] = False
            self._gauge.labels(node=row[0], state=row[1]).set(row[2])

        for node, state_dict in self._possible_combination.items():
            for state, to_set in state_dict.items():
                if to_set:
                    self._gauge.labels(node=node, state=state).set(0)



class ActiveJobClusterGauge:
    def __init__(self, name):
        self._gauge = Gauge(name, "A gauge of current amount of active jobs per cluster",
                            ['state', 'cluster'])
        self._request_per_cluster = """
            SELECT cluster_name,
                count(id) filter(WHERE state = 'running'),
                count(id) filter(WHERE state = 'queued'),
                count(id) filter(WHERE state = 'scheduled')
            FROM job
            WHERE state in ('running', 'queued', 'scheduled')
            GROUP BY cluster_name
        """

        self._request_total = """
            SELECT count(id) filter(WHERE state = 'running'),
                   count(id) filter(WHERE state = 'queued'),
                   count(id) filter(WHERE state = 'scheduled')
            FROM job
            WHERE state in ('running', 'queued', 'scheduled')
        """

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


class CPUCapacity:

    def __init__(self, name):
        self._gauge = Gauge(name, "A gauge of cpu capacity per cluster",
                            ['cluster'])
        self._cpu_per_cluster = """
            SELECT cpu_capacity, name FROM cluster
        """

    def update(self, conn):
        per_cluster = execute_sql(conn, self._cpu_per_cluster, None)

        for cluster_values in per_cluster:
            self._gauge.labels(cluster=cluster_values['name']).set(cluster_values['cpu_capacity'])


class CPUUsage:
    def __init__(self, name):
        self._gauge = Gauge(name, "CPU usage per cluster",
                            ['cluster'])
        self._cpu_per_cluster = """
            SELECT cluster_name, 
            sum((j.definition#>>'{resources,limits,cpu}')::float::float*100) cpu_usage
			FROM job j 
			WHERE j.state = 'running'
			GROUP BY cluster_name
        """

    def update(self, conn):
        per_cluster = execute_sql(conn, self._cpu_per_cluster, None)

        for cluster_values in per_cluster:
            self._gauge.labels(cluster=cluster_values['cluster_name']).set(cluster_values['cpu_usage'])


class MemoryCapacity:
    def __init__(self, name):
        self._gauge = Gauge(name, "A gauge of memory capacity per cluster",
                            ['cluster'])
        self._memory_per_cluster = """
             SELECT memory_capacity, name 
             FROM cluster
             GROUP BY name
        """

    def update(self, conn):
        per_cluster = execute_sql(conn, self._memory_per_cluster, None)

        for cluster_values in per_cluster:
            self._gauge.labels(cluster=cluster_values['name']).set(cluster_values['memory_capacity'])


class MemoryUsage:
    def __init__(self, name):
        self._gauge = Gauge(name, "Memory usage per cluster",
                            ['cluster'])
        self._memory_per_cluster = """
            SELECT cluster_name, sum((j.definition#>>'{resources,limits,memory}')::float::float*100) memory_usage
            FROM job j
            WHERE j.state = 'running'
            GROUP BY cluster_name  
        """

    def update(self, conn):
        per_cluster = execute_sql(conn, self._memory_per_cluster, None)

        for cluster_values in per_cluster:
            self._gauge.labels(cluster=cluster_values['cluster_name']).set(cluster_values['memory_usage'])


class NodesCount:
    def __init__(self, name):
        self._gauge = Gauge(name, "A gauge of the quantity of nodes per cluster",
                            ['cluster'])
        self._nodes_per_cluster = """
            SELECT nodes, name 
            FROM cluster
            GROUP BY name
        """

    def update(self, conn):
        per_cluster = execute_sql(conn, self._nodes_per_cluster, None)

        for cluster_values in per_cluster:
            self._gauge.labels(cluster=cluster_values['name']).set(cluster_values['nodes'])


class UserCount:
    def __init__(self, name):
        self._gauge = Gauge(name, "The total number of users registered in the database",
                            ['cluster'])
        self._user_total = """
          SELECT count(id) as user_amount, name
                FROM public.user
                GROUP BY name
        """

    def update(self, conn):
        per_cluster = execute_sql(conn, self._user_total, None)

        for cluster_values in per_cluster:
            self._gauge.labels(cluster=cluster_values['name']).set(cluster_values['user_amount'])


class ClusterCount:
    def __init__(self, name):
        self._gauge = Gauge(name, "A gauge of the amount of clusters",
                            ['cluster'])
        self._amount_of_clusters = """
            SELECT count(name) as cluster_amount, name
            FROM cluster
            Group by name
        """

    def update(self, conn):
        per_cluster = execute_sql(conn, self._amount_of_clusters, None)
        print(per_cluster)
        for cluster_values in per_cluster:
            print(cluster_values)
            self._gauge.labels(cluster=cluster_values['name']).set(cluster_values['cluster_amount'])


class ProjectCount:
    def __init__(self, name):
        self._gauge = Gauge(name, "The total number of projects registered in the database",
                            ['cluster'])
        self._projects_amount = """
          SELECT count(id) as project_amount, type
                FROM project
                GROUP BY type
        """

    def update(self, conn):
        per_cluster = execute_sql(conn, self._projects_amount, None)

        for cluster_values in per_cluster:
            self._gauge.labels(cluster=cluster_values['type']).set(cluster_values['project_amount'])


class NodeList:
    #returns zero values, but works

    def __init__(self, name):
        self._gauge = Gauge(name,
                            "List of the node_name referenced by the job table for this cluster. This table only shows Node with active job (ie running, queued, scheduled)",
                            ['cluster'])
        self._nodes_per_cluster = """
            SELECT node_name, count(id) FILTER(WHERE state = 'running') as job_amount
			FROM job 
			WHERE node_name is not null 
			AND state IN ('running', 'scheduled', 'queued')
			GROUP BY node_name
        """

    def update(self, conn):
        per_cluster = execute_sql(conn, self._nodes_per_cluster, None)

        for cluster_values in per_cluster:
            self._gauge.labels(cluster=cluster_values['node_name']).set(cluster_values['job_amount'])


class BuildInspector:
    #doesn't work
    def __init__(self, name):
        self._gauge = Gauge(name,
                            "A list of all the jobs of the inspected build.",
                            ['cluster'])
        self._resources_per_job = """
            select name, id, (j.definition#>>'{resources,limits,memory}')::float as memory, (j.definition#>>'{resources,limits,cpu}')::float as cpu
            from job j
        """

    def update(self, conn):
        per_cluster = execute_sql(conn, self._resources_per_job, None)
        print(per_cluster)

        for cluster_values in per_cluster:
            print(cluster_values)
            self._gauge.labels(cluster=cluster_values['name']).set(cluster_values['memory'])


class BuildsTimeRange:
    #not yet tested, but doesn't show errors
    def __init__(self, name):
        self._gauge = Gauge(name,
                            "Average of the Success Rate of each build of the project.. ",
                            ['project'])
        self._request_per_project = """
            SELECT AVG(foo.success_rate_7d) FROM (
SELECT 
  CASE
	  count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued'))
  WHEN
	  0
  THEN
		NULL
  ELSE 
		(count(j.id) filter (where j.state = 'finished'))::float / (count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued')))::float
  END as success_rate_7d
FROM job j
WHERE $__timeFilter(j.end_date) AND j.project_id = (select id from project where name = '[[pname]]')
GROUP BY build_id) as foo
        """
    # GROUP BY project_name, not just name
    #not as it should be
    def update(self, conn):
        per_project = execute_sql(conn, self._request_per_project, None)

        for project_values in per_project:
            self._gauge.labels(project=project_values['build_amount']).set(project_values['build_amount'])

class Job_Inspector_CPU_Use:
    #not yet tested
    #not finished yet
    #doing this with JSON?
    def __init__(self, name):
        self._gauge = Gauge(name,
                            "Graphical representation of the CPU frequency of the job as registered in the database.",
                            ['job'])
        self._cpu_per_job = """
            SELECT
            cpu::float*1024 as cpu
            FROM (
            select to_timestamp((elm)::text::int) as date, elm::text as cpu from (
         select
             j.stats as elm
        FROM
            job j
           ) as foo2 order by date asc
          ) as foo
  
        """

    def update(self, conn):
        per_job = execute_sql(conn, self._cpu_per_job, None)

        for job_values in per_job:
            self._gauge.labels(job=job_values['cpu']).set(job_values['cpu'])

class Job_Memory:
    def __init__(self, name, conn):
        self._gauge = Gauge(name, "A gauge of allocated ressources of running jobs over time",
                            ['job'])
        self._request_total = """
  mem::float as used,
  mem_j_limit as job_limit
FROM (
  elm::jsonb->>'mem'::text as mem, mem_j_limit from (
    select
      jsonb_array_elements(j.stats::jsonb->'[[id]]') as elm, sum((definition#>>'{resources,limits,memory}')::integer) as mem_j_limit
    FROM
      job j
    ) as foo2 
) as foo
        """

        self._request_possible_job = "SELECT DISTINCT name FROM job  ORDER BY  name"
        self._possible_combination = None
        self._possible_job = None
        self._count_to_update = 10
        self._create_combination_dict(conn)

    # Welche Typumwandlungen brauche ich
    # brauch ich die Zeit?
    def _create_combination_dict(self, conn):
        """
        Completely rewrite the combination dict based on the occurrences of the request results without any
        data loss checks made on old cluster or project occurrences.
        """
        self._possible_job = execute_sql(conn, self._request_possible_job, None)

        self._possible_combination = dict()
        for job in self._possible_job:
            if job[0]:
                project_dict = dict()
                for project in self._possible_project:
                    if project[0]:
                        project_dict[project[0]] = True
                self._possible_combination[cluster[0]] = project_dict

    def _update_combination_dict(self, conn):
        """
        Check if the dict must be updated with new values and updates it if necessary.
        To do so we overwrite old values as well as the new ones => check before.

        IT DOES NOT set old values to True (the existence test among list is not efficient),
        we still need to reset all the values by calling _reset_combination_dict
        """
        tmp_possible_cluster = execute_sql(conn, self._request_possible_job, None)

        if AllocatedRscGauge._different_instance_list(self._possible_job, tmp_possible_job):
            print("=== DICT UPDATE - AVOIDABLE COST ===")
            for cluster in self._possible_cluster:
                if cluster[0]:
                    project_dict = self._possible_combination.get(cluster[0])
                    if not project_dict:
                        project_dict = dict()
                        self._possible_combination[cluster[0]] = project_dict
                    for project in self._possible_project:
                        if project[0]:
                            project_dict[project[0]] = True

    def _reset_combination_dict(self):
        """
        Set all the occurrences of the combination dict to True in order to detect which values to set to 0
        because they are missing in the request result
        """
        for project_dict in self._possible_combination.values():
            for project_name in project_dict.keys():
                project_dict[project_name] = True

    @staticmethod
    def _different_instance_list(first, second):
        """
        Return True if the given contains a difference in there occurrences.
        Used to detect if we should update the combination dictionary.
        Example : a new project or a new cluster appeared in the DB
        """
        length = len(first)
        if length != len(second):
            return True
        else:
            for i in range(length):
                if first[i][0] != second[i][0]:
                    return True
        return False

    def update(self, conn):
        total = execute_sql(conn, self._request_total, None)
        if self._count_to_update == 0:
            self._update_combination_dict(conn)
            self._count_to_update = 10
        self._reset_combination_dict()
        self._set_values(total)
        self._count_to_update -= 1

    def _set_values(self, per_cluster, total):

        for row in total:
            project_dict = self._possible_combination.get("'%'")
            if project_dict and project_dict.get(row[0]):
                project_dict[row[0]] = False

            self._gauge.labels(rsc="mem", cluster="'%'", project=row[0]).set(row[1])
            self._gauge.labels(rsc="cpu", cluster="'%'", project=row[0]).set(row[2])

        for cluster, project_dict in self._possible_combination.items():
            to_delete = []
            for project, not_used in project_dict.items():
                if not_used:
                    to_delete.append(project)
                    self._gauge.labels(rsc="mem", cluster=cluster, project=project).set(0)
                    self._gauge.labels(rsc="cpu", cluster=cluster, project=project).set(0)

            # Maybe it was the last occurrence ever of this datas. We delete it in order to keep the combination dict
            # as small as possible (would be running for entire weeks maybe)
            for maybe_last_occurrence in to_delete:
                del project_dict[maybe_last_occurrence]


class Jobs_success_rate:
    def __init__(self, name):
        self._gauge = Gauge(name, "Success rate for all the jobs of the project.",
                            ['cluster', 'project'])
        self._request_per_project = """
            SELECT 
  CASE
	  count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued'))
  WHEN
	  0
  THEN
		NULL
  ELSE 
		(count(j.id) filter (where j.state = 'finished'))::float / (count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued')))::float
  END as success_rate_7d
FROM job j
WHERE $__timeFilter(j.end_date) AND j.project_id = (select id from project where name = '[[pname]]')
        """

    def update(self, conn):
        per_cluster = execute_sql(conn, self._amount_of_clusters, None)
        print(per_cluster)
        for cluster_values in per_cluster:
            print(cluster_values)
            self._gauge.labels(cluster=cluster_values['name']).set(cluster_values['cluster_amount'])


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
    server_port = os.environ.get('INFRABOX_PORT', 8000)

    # Copied from review.py, could be changed over time
    conn = connect_db()
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    # When restarting or starting on a docker container, the port can be still used at the first try
    if not start_server(2, 5, server_port):
        return 1

    active_job_gauge = ActiveJobClusterGauge('job_active_current_count')
    rsc_gauge = AllocatedRscGauge('rsc_current_count', conn)
    all_job_gauge = AllJobNodeGauge('job_all_node_count')
    cpu_capacity = CPUCapacity('cpu_capacity_per_cluster')
    cpu_usage = CPUUsage('cpu_usage_per_cluster')
    memory_capacity = MemoryCapacity('memory_capacity_per_cluster')
    memory_usage = MemoryUsage('memory_usage_per_cluster')
    nodes_quantity = NodesCount('nodes_quantity_per_cluster')
    user_count = UserCount('user_amount') #works
    cluster_count = ClusterCount('cluster_amount') #works
    project_count = ProjectCount('project_amount')
    node_list = NodeList('node_list_per_cluster')
    build_inspector = BuildInspector('jobs_of_build')
    builds__over_time_range = BuildsTimeRange('builds_over_time_range')
    job_cpu = Job_Inspector_CPU_Use('cpu_per_job')
    #job_memory = Job_Memoy_Gauge('job_memory')


    while running:
        try:
            active_job_gauge.update(conn)
            rsc_gauge.update(conn)
            all_job_gauge.update(conn)
            print('test')
            cpu_capacity.update(conn)
            cpu_usage.update(conn)
            memory_capacity.update(conn)
            memory_usage.update(conn)
            nodes_quantity.update(conn)
            user_count.update(conn)
            cluster_count.update(conn)
            project_count.update(conn)
            #node_list.update(conn)
            #builds__over_time_range.update(conn)
          #doesn't work  build_inspector.update(conn)
            # job_cpu.update(conn)
         #   job_memory.update(conn)


        except psycopg2.OperationalError:
            # the db connection closed unexpectedly
            conn = connect_db()
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        # experimental value
        time.sleep(1.3)


if __name__ == '__main__':
    running = True
    main()


