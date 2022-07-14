from flask import request, g, abort
from flask_restx import Resource, fields

from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model

ns = api.namespace('Pattern',
                   path='/api/v1/projects/<project_id>/pattern',
                   description='Project skip Pattern')

project_skip_pattern_model = api.model('Pattern', {
    'id': fields.String(required=False),
    'skip_pattern': fields.String(required=True)
})


@ns.route('/')
@api.doc(responses={403: 'Not Authorized'})
class Pattern(Resource):

    @api.marshal_with(project_skip_pattern_model)
    def get(self, project_id):
        '''
        Returns project's skip pattern
        '''
        v = g.db.execute_many_dict('''
            SELECT id, skip_pattern
            FROM project_skip_pattern
            WHERE project_id = %s
        ''', [project_id])
        return v

    @api.expect(project_skip_pattern_model)
    def post(self, project_id):
        v = g.db.execute_many_dict('''
            SELECT skip_pattern
            FROM project_skip_pattern
            WHERE project_id = %s
        ''', [project_id])
        if v:
            return abort(400, 'Pattern already exists.')
        b = request.get_json()
        g.db.execute('''
                    INSERT INTO project_skip_pattern (project_id, skip_pattern) VALUES(%s, %s)
                ''', [project_id, b['skip_pattern']])
        g.db.commit()
        return OK('Successfully added skip_pattern.')

    @api.response(200, 'Success', response_model)
    def delete(self, project_id):
        g.db.execute('''
                    DELETE FROM project_skip_pattern WHERE project_id = %s
                ''', [project_id])
        g.db.commit()
        return OK('Successfully deleted skip_pattern.')
