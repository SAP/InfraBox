#!/usr/bin/env python
import os

import eventlet
from eventlet import wsgi
eventlet.monkey_patch()

from flask import request, g, jsonify
from pyinfraboxutils.ibflask import app
app.config['OPA_ENABLED'] = False

from pyinfraboxutils import get_env, get_logger
from pyinfraboxutils.db import connect_db
import json

@app.route('/')
def health_check():
    return 'This datasource is healthy.'


@app.route('/search', methods=['POST'])
def search():
    print(request.get_json())
    # returns a list of targets that can be chosen in queries to the Simple JSON datasource
    #targets = find_targets()
    #return jsonify(targets)
    return jsonify(["project_list"],["job_list"], ["cluster_overview"], ["job_inspector_message"], ["node_list"], ["job_inspector_information"],
                   ["job_inspector_memory"], ["job_inspector_cpu"], ["node_inspector_unexp_term_killed"],
                ["node_inspector_unexp_term_failure"], ["node_inspector_unexp_term_error"], ["build_list"],["projects_running_jobs"], ["project_inspector_information"], ["AVG_Build_Success_Rate"],
                   ["Jobs_Success_Rate"], ["Builds_Over_Time_Range"])

def convert(result, columns=[]):
    d = {
        "columns": columns,
        "rows": [],
        "type": "table"
    }

    for row in result:
        r = []
        for c in columns:
            r.append(row[c['text']])

        d['rows'].append(r)

    return [d]

@app.route('/query', methods=['POST'])
def query():
    d = request.get_json()
    print(json.dumps(d, indent=4))

    metric = d['targets'][0]['target']

    if metric == 'project_list':
        r = g.db.execute_many("""
            SELECT 	p.name, p.type, p.public, 
	j_infos.jobs_runnings as jobs_runnings,
	j_infos.failed_jobs_7d as failed_jobs_7d,
	j_infos.success_rate_7d as success_rate_7d,
	c_infos.collabs as collabs,
	j_infos.avg_cpu as avg_cpu,
	j_infos.min_cpu as min_cpu,
	j_infos.max_cpu as max_cpu,
	j_infos.avg_mem as avg_mem,
	j_infos.min_mem as min_mem,
	j_infos.max_mem as max_mem,
	p.id
FROM project p LEFT OUTER JOIN 
(SELECT
	j.project_id,
	count(j.id) filter (where j.state = 'running') as jobs_runnings,
	count(j.id) filter (where (j.state IN ('failure', 'error')) and j.end_date between %(from)s and %(to)s) as failed_jobs_7d,
	CASE
	  count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued') and j.end_date between %(from)s and %(to)s)
	WHEN
	  0
	THEN
		NULL
	ELSE 
		(count(j.id) filter (where (j.state = 'finished' and j.end_date between %(from)s and %(to)s)))::float / (count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued') and j.end_date between %(from)s and %(to)s))::float
	END as success_rate_7d,
	avg((j.definition#>>'{resources,limits,cpu}')::float) filter (where j.end_date between %(from)s and %(to)s OR j.state = 'running') as avg_cpu,
	min((j.definition#>>'{resources,limits,cpu}')::float) filter (where j.end_date between %(from)s and %(to)s OR j.state = 'running') as min_cpu,
	max((j.definition#>>'{resources,limits,cpu}')::float) filter (where j.end_date between %(from)s  and %(to)s OR j.state = 'running') as max_cpu,
	avg((j.definition#>>'{resources,limits,memory}')::float) filter (where j.end_date between %(from)s  and %(to)s OR j.state = 'running') as avg_mem,
	min((j.definition#>>'{resources,limits,memory}')::float) filter (where j.end_date between %(from)s and %(to)s OR j.state = 'running') as min_mem,
	max((j.definition#>>'{resources,limits,memory}')::float) filter (where j.end_date between %(from)s  and %(to)s OR j.state = 'running') as max_mem
FROM
	job j
 GROUP BY
	j.project_id) j_infos ON p.id = j_infos.project_id
LEFT JOIN
(SELECT project_id, count(user_id) as collabs FROM collaborator GROUP BY project_id) c_infos ON p.id = c_infos.project_id 
        """, {
            'from': d['range']['from'],
            'to': d['range']['to']
        })

        result = convert(r, columns=[
              {"text": "name","type":"string"},
              {"text": "type", "type": "string"},
              {"text": "public", "type": "string"},
              {"text": "jobs_runnings", "type": "string"},
              {"text": "failed_jobs_7d", "type": "string"},
              {"text": "success_rate_7d", "type": "string"},
              {"text": "collabs", "type": "string"},
              {"text": "avg_cpu", "type": "string"},
              {"text": "min_cpu", "type": "string"},
              {"text": "max_cpu", "type": "string"},
              {"text": "avg_mem", "type": "string"},
              {"text": "min_mem", "type": "string"},
              {"text": "max_mem", "type": "string"},
              {"text": "id", "type": "string"}
            ])
        print(result)
        return jsonify(result)

    if metric == 'job_list':

            r = g.db.execute_many("""
select p.name as p_name, b.build_number, b.restart_counter, j.name as j_name, (j.definition#>>'{resources,limits,memory}')::float as memory, (j.definition#>>'{resources,limits,cpu}')::float as cpu, j.id 
from project p, build b, job j 
where p.id = j.project_id AND b.id = j.build_id AND b.id = %(bid)s
            """, {
                'bid': d['scopedVars']['bid']['value']
            })

            result = convert(r, columns=[
                {"text": "p_name", "type": "string"},
                {"text": "build_number", "type": "string"},
                {"text": "restart_counter", "type": "string"},
                {"text": "j_name", "type": "string"},
                {"text": "memory", "type": "string"},
                {"text": "cpu", "type": "string"},
                {"text": "id", "type": "string"}
            ])
            print(result)
            return jsonify(result)

    if metric == 'cluster_overview':
        r = g.db.execute_many("""
SELECT c.name, c.nodes, count(j.id) filter (WHERE j.state = 'running') as running,
  count(j.id) filter (WHERE j.state = 'scheduled') as scheduled,
  count(j.id) filter (WHERE j.state = 'queued') as queued,
  (sum((j.definition#>>'{resources,limits,cpu}')::float) FILTER (WHERE j.state = 'running' ))::float / c.cpu_capacity as cpu_use, 
  (sum((j.definition#>>'{resources,limits,memory}')::float) filter (WHERE j.state = 'running'))::float / c.memory_capacity * 1024 as mem_use
FROM cluster c LEFT OUTER JOIN job j
ON c.name = j.cluster_name
GROUP BY c.name
                """,)

        result = convert(r, columns=[
            {"text": "name", "type": "string"},
            {"text": "nodes", "type": "string"},
            {"text": "running", "type": "string"},
            {"text": "scheduled", "type": "string"},
            {"text": "queued", "type": "string"},
            {"text": "cpu_use", "type": "string"},
            {"text": "mem_use", "type": "string"}
        ])
        print(result)
        return jsonify(result)

    if metric == 'job_inspector_information':
        #returns zero data -> not yet fully tested
        r = g.db.execute_many("""
 SELECT p.name as p_name, b.build_number, b.restart_counter, j.name as j_name, ((j.definition#>>'{resources,limits,cpu}')::float) as cpu, ((j.definition#>>'{resources,limits,memory}')::float) as memory, c.cpu_capacity, c.memory_capacity, j.id
FROM project p, build b, job j, cluster c
WHERE p.id = j.project_id AND b.id = j.build_id AND c.name = j.cluster_name AND j.id = %(id)s
            """, {
            'id': d['scopedVars']['id']['value']
        })

        result = convert(r, columns=[
            {"text": "p_name", "type": "string"},
            {"text": "build_number", "type": "string"},
            {"text": "restart_counter", "type": "string"},
            {"text": "j_name", "type": "string"},
            {"text": "cpu", "type": "string"},
            {"text": "memory", "type": "string"},
            {"text": "cpu_capacity", "type": "string"},
            {"text": "memory_capacity", "type": "string"},
            {"text": "id", "type": "string"}
        ])
        print(result)
        return jsonify(result)

    if metric == 'job_inspector_memory':
            #returns zero data -> not yet fully tested
            #%(now)s == $__time(date) ?
            r = g.db.execute_many("""
     SELECT
  %(now)s,
  mem::float as used,
  mem_j_limit as job_limit
FROM (
  select to_timestamp((elm::jsonb->'date')::text::int) as date, elm::jsonb->>'mem'::text as mem, mem_j_limit from (
    select
      jsonb_array_elements(j.stats::jsonb->%(id)s) as elm, ((j.definition#>>'{resources,limits,memory}')::float) as mem_j_limit
    FROM
      job j
    WHERE 
      j.id = %(id)s
    ) as foo2 order by date asc
) as foo
                """, {
                'id': d['scopedVars']['id']['value'],
                'now': d['range']['to']
            })

            result = convert(r, columns=[
                {"text": "time", "type": "string"},
                {"text": "used", "type": "string"},
                {"text": "job_limit", "type": "string"}
            ])
            print(result)
            return jsonify(result)

    if metric == 'job_inspector_cpu':
        # id as target must be added, at the moment it's project_name #not yet tested
        # When and how is the project id as target transfered
        # %(now)s == $__time(date) ?
        r = g.db.execute_many("""
         SELECT
      %(now)s,
  cpu::float*1024 as cpu
FROM (
  select to_timestamp((elm::jsonb->'date')::text::int) as date, elm::jsonb->>'cpu'::text as cpu from (
    select
      jsonb_array_elements(j.stats::jsonb->%(id)s) as elm
    FROM
      job j
    WHERE 
      j.id = %(id)s
    ) as foo2 order by date asc
) as foo
                    """, {
            'id': d['targets'][0]['data']['project_name'],
            'now': d['range']['to']
        })

        result = convert(r, columns=[
            {"text": "time", "type": "string"},
            {"text": "cpu", "type": "string"}
        ])
        print(result)
        return jsonify(result)

    if metric == 'job_inspector_message':
        #works probably fine, but the selected target id does not deliver a result
        r = g.db.execute_many("""
        select message from job where id = %(id)s
        """, {
            'id': d['scopedVars']['id']['value']
        })

        result = convert(r, columns=[
              {"text": "message", "type": "string"}
            ])
        print(result)
        return jsonify(result)

    if metric == 'node_inspector_unexp_term_killed':
        #not sure, if he query is correct
        #returns zero data
        r = g.db.execute_many("""
        SELECT
  end_date,
  count(id) as Killed
FROM
  job
WHERE
  end_date between %(from)s and %(to)s
  AND state = 'killed'
  AND node_name = %(node)s
  GROUP BY
  end_date
        """, {
            'from': d['range']['from'],
            'to': d['range']['to'],
            'node': d['targets'][0]['data']['project_name']
        })

        result = convert(r, columns=[
            {"text": "date", "type": "string"},
            {"text": "killed", "type": "string"}
            ])
        print(result)
        return jsonify(result)

    if metric == 'node_inspector_unexp_term_failure':
            # not sure, if he query is correct
            # returns zero data
            r = g.db.execute_many("""
            SELECT
      end_date,
      count(id) as Failure
    FROM
      job
    WHERE
      end_date between %(from)s and %(to)s
      AND state = 'failure'
      AND node_name = %(node)s
      GROUP BY
      end_date
            """, {
                'from': d['range']['from'],
                'to': d['range']['to'],
                'node': d['targets'][0]['data']['project_name']
            })

            result = convert(r, columns=[
                {"text": "date", "type": "string"},
                {"text": "Failure", "type": "string"}
            ])
            print(result)
            return jsonify(result)

    if metric == 'node_inspector_unexp_term_error':
        # not sure, if the query is correct
        # returns zero data
        r = g.db.execute_many("""
            SELECT
      end_date,
      coalesce(count(id),0) as Error
    FROM
      job
    WHERE
      end_date between %(from)s and %(to)s
      AND state = 'error'
      AND node_name = %(node)s
      GROUP BY
      end_date
            """, {
            'from': d['range']['from'],
            'to': d['range']['to'],
            'node': d['targets'][0]['data']['project_name']
        })

        result = convert(r, columns=[
            {"text": "date", "type": "string"},
            {"text": "error", "type": "string"}
        ])
        print(result)
        return jsonify(result)

    if metric == 'node_list':
            r = g.db.execute_many("""
    SELECT
	j.cluster_name,
	j.node_name,
	count(j.id) filter (where j.state = 'running') as jobs_running,
	count(j.id) filter (where j.state = 'scheduled') as jobs_scheduled,
	count(j.id) filter (where j.state = 'queued') as jobs_queued,
	count(j.id) filter (where (j.state IN ('failure', 'error')) and j.end_date between %(from)s and %(to)s) as failed_jobs_tr,
	CASE
	  count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued') and j.end_date between %(from)s and %(to)s)
	WHEN
	  0
	THEN
		NULL
	ELSE 
		(count(j.id) filter (where (j.state = 'finished' and j.end_date between %(from)s and %(to)s)))::float / (count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued') and j.end_date between %(from)s and %(to)s))::float
	END as finished_rate_tr,
	CASE
	  count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued') and j.end_date between %(from)s and %(to)s)
	WHEN
	  0
	THEN
		NULL
	ELSE 
		(count(j.id) filter (where (j.state = 'error' and j.end_date between %(from)s and %(to)s)))::float / (count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued') and j.end_date between %(from)s and %(to)s))::float
	END as error_rate_tr,
	CASE
	  count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued') and j.end_date between %(from)s and %(to)s)
	WHEN
	  0
	THEN
		NULL
	ELSE 
		(count(j.id) filter (where (j.state = 'failure' and j.end_date between %(from)s and %(to)s)))::float / (count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued') and j.end_date between %(from)s and %(to)s))::float
	END as failure_rate_tr
FROM
	job j
WHERE 
  j.node_name is not null
GROUP BY
	j.cluster_name, j.node_name
            """, {
                'from': d['range']['from'],
                'to': d['range']['to']
            })

            result = convert(r, columns=[
                {"text": "cluster_name", "type": "string"},
                {"text": "node_name", "type": "string"},
                {"text": "jobs_running", "type": "string"},
                {"text": "jobs_queued", "type": "string"},
                {"text": "failed_jobs_tr", "type": "string"},
                {"text": "finished_rate_tr", "type": "string"},
                {"text": "error_rate_tr", "type": "string"},
                {"text": "failure_rate_tr", "type": "string"}
            ])
            print(result)
            return jsonify(result)


    if metric == 'build_list':
        r = g.db.execute_many("""
SELECT pinfo.name as pname, b.build_number, b.restart_counter, sr.sr, b.id
FROM  (SELECT id, build_number, restart_counter FROM build WHERE project_id = (select id from project where name = %(pname)s)) as b
LEFT OUTER JOIN (SELECT build_id,
  CASE
	  count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued'))
  WHEN
	  0
  THEN
		NULL
  ELSE 
		(count(j.id) filter (where j.state = 'finished'))::float / (count(j.id) filter (where j.state NOT IN ('running', 'scheduled', 'queued')))::float
  END as sr
  FROM job j
  WHERE j.project_id = (select id from project where name = %(pname)s) AND j.end_date between %(from)s and %(to)s
  GROUP BY build_id) as sr
ON sr.build_id = b.id
LEFT JOIN (SELECT name FROM project WHERE  name = %(pname)s) as pinfo ON true
                """, {
            'from': d['range']['from'],
            'to': d['range']['to'],
            'pname': d['scopedVars']['pname']['value']
        })

        result = convert(r, columns=[
            {"text": "pname", "type": "string"},
            {"text": "build_number", "type": "string"},
            {"text": "restart_counter", "type": "string"},
            {"text": "sr", "type": "string"},
            {"text": "id", "type": "string"}
        ])
        print(result)
        return jsonify(result)

    if metric == 'projects_running_jobs':
            r = g.db.execute_many("""
SELECT c.name as cluster, count(j.id) as jobs
FROM cluster c LEFT OUTER JOIN job j 
ON j.state = 'running' ANd j.cluster_name = c.name AND j.project_id = (select id from project where name = %(pname)s)
GROUP BY c.name
                    """, {
                'pname': d['scopedVars']['pname']['value']
            })

            result = convert(r, columns=[
                {"text": "cluster", "type": "string"},
                {"text": "jobs", "type": "string"}
            ])
            print(result)
            return jsonify(result)

    if metric == 'project_inspector_information':

        r = g.db.execute_many("""
Select %(pname)s as name, p.id as id, p.public as public, p.build_on_push as build_on_push, p.build_on_trigger as build_on_trigger, count(c.user_id) as collaborators
from project p LEFT OUTER JOIN collaborator c
ON  c.project_id = p.id
WHERE name = %(pname)s
GROUP BY id """, {
             'pname': d['scopedVars']['pname']['value']
        })

        result = convert(r, columns=[
            {"text": "name", "type": "string"},
            {"text": "id", "type": "string"},
            {"text": "public", "type": "string"},
            {"text": "build_on_push", "type": "string"},
            {"text": "build_on_trigger", "type": "string"},
            {"text": "collaborators", "type": "string"}
        ])
        print(result)
        return jsonify(result)


    if metric == 'AVG_Build_Success_Rate':
            r = g.db.execute_many("""
SELECT AVG(foo.success_rate_7d) as success FROM (
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
WHERE j.end_date between %(from)s and %(to)s AND j.project_id = (select id from project where name = %(pname)s)
GROUP BY build_id) as foo """, {
                'from': d['range']['from'],
                'to': d['range']['to'],
                'pname': d['scopedVars']['pname']['value']
            })

            result = convert(r, columns=[
                {"text": "success", "type": "string"}
            ])
            print(result)
            return jsonify(result)

    if metric == 'Jobs_Success_Rate':
        r = g.db.execute_many("""
SELECT foo.success_rate_7d  as success FROM (
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
WHERE j.end_date between %(from)s and %(to)s AND j.project_id = (select id from project where name = %(pname)s)) as foo""", {
            'from': d['range']['from'],
            'to': d['range']['to'],
            'pname': d['scopedVars']['pname']['value']
        })

        result = convert(r, columns=[
            {"text": "success", "type": "string"}
        ])
        print(result)
        return jsonify(result)

    if metric == 'Builds_Over_Time_Range':
            r = g.db.execute_many("""
SELECT count(DISTINCT build_id) as builds
FROM job
WHERE project_id = (select id from project where name = %(pname)s) AND end_date between %(from)s and %(to)s AND state NOT IN ('running', 'scheduled', 'queued')""",
                                  {
                                      'from': d['range']['from'],
                                      'to': d['range']['to'],
                                      'pname': d['scopedVars']['pname']['value']
                                  })

            result = convert(r, columns=[
                {"text": "builds", "type": "string"}
            ])
            print(result)
            return jsonify(result)

    else:
        return jsonify([])



    #req = request.get_json()
    # SQL requests to Postgres must be implemented here
    # the data must be requested depending on the data

    # alternative way
    #conn = connect_db()
    #target = req.get('target', '*')
    # bei query evtl reverenz auf target
    #if class (read from url) == project-inspector_informations -> result == query2
    #query = conn.execute("select message from job where id = %d" %int(id)) #insert job as a target? #id = id from target
    #result = {'data': [dict(zip(tuple(query.keys()), i)) for i in query.cursor]}
    #return jsonify(result)


def find_targets():
    # Brauch man das? cur = conn.cursor()
    # do several target classes depending on the dashboard. But how?
    # if a single cluster is a target

    all_targets = """"
 SELECT cluster.name, project.name, node.name 
 FROM cluster, project, node
 """
    # param = ("Faro", "2013-12-01", "2013-12-05")
    conn.execute_sql(conn, all_targets, None)
    return jsonify(data=conn.fetchall()) #or cur.fetchall

    return data.json_encoder()


def main():
    # getting the env variables
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_DB')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_PORT')
    server_port = os.environ.get('INFRABOX_PORT', 8080)

    connect_db() # Wait until DB is ready
    wsgi.server(eventlet.listen(('0.0.0.0', server_port)), app)

if __name__ == '__main__':
    main()
