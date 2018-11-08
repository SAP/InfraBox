from flask import request, g, abort
from flask_restplus import Resource

from pyinfrabox.utils import validate_uuid
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api
from pyinfraboxutils.token import encode_project_token


from pyinfraboxutils import get_logger
logger = get_logger('api')


@api.route('/api/v1/admin/quotas/<quota_type>', doc=False)
class Quotas(Resource):

    def get(self, quota_type):
        '''
        Returns quotas
        '''

        p = g.db.execute_many_dict('''
            SELECT name, value, id, object_id, description
            FROM quotas
            WHERE object_type = '%s'
            ORDER BY name
        ''' % (quota_type))

        return p

    def post(self, quota_type):
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
            INSERT INTO quotas (value, object_id, object_type, name, description)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, [b['value'], b['object_id'], quota_type, b['name'], b['description']])

        quota_id = result['id']
        quota = encode_project_token(quota_id, b['object_id'])

        g.db.commit()

        return OK('Successfully added quota.', {'quota': quota})

@api.route('/api/v1/admin/quotas/users/<user_id>', doc=False)
class QuotasUser(Resource):

    def get(self, user_id):
        '''
        Returns quotas
        '''
        p = g.db.execute_many_dict('''
            SELECT name, value, id, object_id, description
            FROM quotas
            WHERE object_id = %s OR object_id = 'default_value_user'
            ORDER BY name
        ''', [user_id])

        return p

@api.route('/api/v1/admin/quotas/objects_id/<object_type>', doc=False)
class ObjectsID(Resource):

    def get(self, object_type):
        '''
        Returns objects id
        '''
        p = g.db.execute_many_dict('''
            SELECT id, name
            FROM public.%s
            ORDER BY name
        ''' % (object_type))

        return p

@api.route('/api/v1/admin/quota/<quota_id>', doc=False)
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



    def post(self, quota_id):
        '''
        Update a quota
        '''

        b = request.get_json()

        if not validate_uuid(quota_id):
            abort(400, "Invalid quota uuid.")

        num_tokens = g.db.execute_one("""
            SELECT COUNT(*) FROM quotas
            WHERE id = %s
        """, [quota_id])[0]

        if num_tokens == 0:
            return abort(404, 'Such quota does not exist.')

        g.db.execute('''
            UPDATE quotas
            SET value = %s,
                description = %s
            WHERE id = %s
        ''', [str(b['value']), str(b['description']), quota_id])


        g.db.commit()

        return OK('Successfully updated quota.')


        

