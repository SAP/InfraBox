import re

from flask import request, g, abort
from flask_restplus import Resource, fields

from pyinfrabox.utils import validate_uuid
from pyinfraboxutils.ibflask import auth_required, OK
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.secrets import encrypt_secret
from api.namespaces import project as ns

secret_model = api.model('Secret', {
    'name': fields.String(required=True),
    'id': fields.String(required=True),
})

add_secret_model = api.model('AddSecret', {
    'name': fields.String(required=True, max_length=255),
    'value': fields.String(required=True, max_length=1024 * 128),
})

@ns.route('/<project_id>/secrets/')
class Secrets(Resource):

    name_pattern = re.compile('^[a-zA-Z0-9_]+$')

    @auth_required(['user'])
    @api.marshal_list_with(secret_model)
    def get(self, project_id):
        p = g.db.execute_many_dict('''
            SELECT name, id FROM secret
            WHERE project_id = %s
        ''', [project_id])
        return p

    @auth_required(['user'])
    @api.expect(add_secret_model)
    def post(self, project_id):
        b = request.get_json()

        if not Secrets.name_pattern.match(b['name']):
            abort(400, 'Secret name must be not empty alphanumeric string.')

        result = g.db.execute_one_dict("""
            SELECT COUNT(*) as cnt FROM secret WHERE project_id = %s
        """, [project_id])

        if result['cnt'] > 50:
            abort(400, 'Too many secrets.')

        r = g.db.execute_one("""
                    SELECT count(*) FROM secret
                    WHERE project_id = %s AND name = %s
                """, [project_id, b['name']])

        if r[0] > 0:
            abort(400, 'Secret with this name already exist.')

        value = encrypt_secret(b['value'])

        g.db.execute('''
            INSERT INTO secret (project_id, name, value) VALUES(%s, %s, %s)
        ''', [project_id, b['name'], value])

        g.db.commit()

        return OK('Successfully added secret.')


@ns.route('/<project_id>/secrets/<secret_id>')
class Secret(Resource):
    @auth_required(['user'])
    def delete(self, project_id, secret_id):
        if not validate_uuid(secret_id):
            abort(400, "Invalid secret uuid.")

        num_secrets = g.db.execute_one("""
            SELECT COUNT(*) FROM secret
            WHERE project_id = %s and id = %s
        """, [project_id, secret_id])[0]

        if num_secrets == 0:
            return abort(400, 'Such secret does not exist.')

        g.db.execute("""
            DELETE FROM secret WHERE project_id = %s and id = %s
        """, [project_id, secret_id])
        g.db.commit()

        return OK('Successfully deleted secret.')
