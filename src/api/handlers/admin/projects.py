from flask import g, abort, request
from flask_restplus import Resource, fields

from pyinfraboxutils.ibrestplus import api

from api.namespaces import admin as ns

@ns.route('/projects/')
class Projects(Resource):

    def get(self):
        projects = g.db.execute_many_dict('''
            SELECT id, name, type, public
            FROM project
            ORDER BY name
        ''')

        result = {}

        for p in projects:
            result[p['name']] = p

        collabs = g.db.execute_many_dict('''
            SELECT count(*) as cnt, p.name
            FROM project p
            JOIN collaborator c
            ON c.project_id = p.id
            GROUP BY p.name
        ''')

        for c in collabs:
            result[c['name']]['collaborators'] = c['cnt']

        builds = g.db.execute_many_dict('''
            SELECT count(*) as cnt, p.name
            FROM project p
            JOIN build b
            ON b.project_id = p.id
            GROUP BY p.name
        ''')

        for b in builds:
            result[b['name']]['builds'] = b['cnt']

        jobs = g.db.execute_many_dict('''
            SELECT count(*) as cnt, p.name
            FROM project p
            JOIN job j
            ON j.project_id = p.id
            GROUP BY p.name
        ''')

        for j in jobs:
            result[j['name']]['jobs'] = j['cnt']

        response = []
        for _, v in result.iteritems():
            response.append(v)

        return response
