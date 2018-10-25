from flask import request, g, abort
from flask_restplus import Resource

from pyinfrabox.utils import validate_uuid
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_project_token

@api.route('/api/v1/admin/quotas', doc=False)
class Quotas(Resource):

    def get(self):
        '''
        Returns quotas
        '''
        p = g.db.execute_many_dict('''
            SELECT name, value, id, object_id
            FROM quotas
            ORDER BY name
        ''')

        return p

    def post(self):
        '''
        Create new quota
        '''
        b = request.get_json()

        if b['object_id'] == "default_value":
            return abort(400, 'You cant create quota with default_value as object_id !')

        result = g.db.execute_one("""
            SELECT COUNT(*) FROM quotas
            WHERE object_id = %s AND name = %s
        """, [b['object_id'], b['name']])[0]

        if result != 0:
            return abort(400, 'Quota with such a name already exists.')

        result = g.db.execute_one_dict("""
            INSERT INTO quotas (value, object_id, name)
            VALUES (%s, %s, %s) RETURNING id
        """, [b['value'], b['object_id'], b['name']])

        quota_id = result['id']
        quota = encode_project_token(quota_id, b['object_id'])

        g.db.commit()

        return OK('Successfully added quota.', {'quota': quota})


@api.route('/api/v1/admin/quotas/<quota_id>', doc=False)
class Quota(Resource):

    def delete(self, quota_id):
        '''
        Delete a quota
        '''
        if not validate_uuid(quota_id):
            abort(400, "Invalid quota uuid.")

        num_tokens = g.db.execute_one("""
            SELECT COUNT(*) FROM quotas
            WHERE id = %s
        """, [quota_id])[0]

        if num_tokens == 0:
            return abort(404, 'Such quota does not exist.')

        g.db.execute("""
                     DELETE FROM quotas
                     WHERE id = %s
        """, [quota_id])
        g.db.commit()

        return OK('Successfully deleted quota.')
