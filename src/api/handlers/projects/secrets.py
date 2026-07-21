import re
import hashlib
import secrets as secrets_lib
from datetime import datetime, timezone, timedelta

from flask import request, g, abort
from flask_restx import Resource, fields


from pyinfrabox.utils import validate_uuid
from pyinfraboxutils.ibflask import OK
from pyinfraboxutils.ibrestplus import api, response_model
from pyinfraboxutils.secrets import encrypt_secret, decrypt_secret

ns = api.namespace('Secrets',
                   path='/api/v1/projects/<project_id>/secrets',
                   description='Secret related operations')

# Temporary read-token for decrypted secret values.
# Format: ib_secret_read_<48 hex chars>; lookup key is the first 16 hex chars
# of the suffix; only the SHA-256 hash of the raw token is stored.
_READ_TOKEN_PREFIX = 'ib_secret_read_'
_READ_TOKEN_HEADER = 'X-Secret-Read-Token'
_READ_TOKEN_TTL_MINUTES = 20


def _utcnow_naive():
    '''Naive UTC datetime for comparing against psycopg2 TIMESTAMP values.'''
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _hash_read_token(raw_token):
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

secret_model = api.model('Secret', {
    'name': fields.String(required=True),
    'id': fields.String(required=True),
})

add_secret_model = api.model('AddSecret', {
    'name': fields.String(required=True, max_length=255),
    'value': fields.String(required=True, max_length=1024 * 128),
})

@ns.route('/')
@api.doc(responses={403: 'Not Authorized'})
class Secrets(Resource):

    name_pattern = re.compile('^[a-zA-Z0-9_]+$')

    @api.marshal_list_with(secret_model)
    def get(self, project_id):
        '''
        Returns project's secrets
        '''
        p = g.db.execute_many_dict('''
            SELECT name, id FROM secret
            WHERE project_id = %s
        ''', [project_id])
        return p

    @api.expect(add_secret_model)
    @api.response(200, 'Success', response_model)
    def post(self, project_id):
        '''
        Create new secret
        '''
        b = request.get_json()

        if not Secrets.name_pattern.match(b['name']):
            abort(400, 'Secret name must be not empty alphanumeric string.')

        result = g.db.execute_one_dict("""
            SELECT COUNT(*) as cnt FROM secret WHERE project_id = %s
        """, [project_id])

        if result['cnt'] > 200:
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


@ns.route('/<secret_id>')
@api.doc(responses={403: 'Not Authorized'})
class Secret(Resource):
    @api.response(200, 'Success', response_model)
    def delete(self, project_id, secret_id):
        '''
        Delete a secret
        '''
        if not validate_uuid(secret_id):
            abort(400, "Invalid secret uuid.")

        num_secrets = g.db.execute_one("""
            SELECT COUNT(*) FROM secret
            WHERE project_id = %s and id = %s
        """, [project_id, secret_id])[0]

        if num_secrets == 0:
            return abort(400, 'Such secret does not exist.')

        num_keys = g.db.execute_one("""
            SELECT COUNT(*) FROM sshkey
            WHERE project_id = %s and secret_id = %s
        """, [project_id, secret_id])[0]

        if num_keys != 0:
            return abort(400, 'Secret is still used SSH Key.')

        g.db.execute("""
            DELETE FROM secret WHERE project_id = %s and id = %s
        """, [project_id, secret_id])
        g.db.commit()

        return OK('Successfully deleted secret.')


secret_value_model = api.model('SecretValue', {
    'name': fields.String(required=True),
    'value': fields.String(required=True),
})

read_token_model = api.model('SecretReadToken', {
    'token': fields.String(required=True),
    'expires_at': fields.String(required=True),
})


def _validate_read_token(project_id):
    '''
    Validate the temporary read-token presented in the X-Secret-Read-Token
    header for the given project. Aborts with 401/403 when invalid; returns
    the token row on success.

    This is the second factor for reading decrypted secret values: OPA has
    already confirmed the caller is a project administrator, and this confirms
    the caller holds a valid, unexpired read-token bound to this project and
    to themselves.
    '''
    raw_token = request.headers.get(_READ_TOKEN_HEADER, '')

    if not raw_token.startswith(_READ_TOKEN_PREFIX):
        abort(401, 'A secret read-token is required. Apply for one first.')

    token_suffix = raw_token[len(_READ_TOKEN_PREFIX):]
    if len(token_suffix) != 48:
        abort(401, 'Invalid read-token format.')

    token_id = token_suffix[:16]
    token_hash = _hash_read_token(raw_token)

    row = g.db.execute_one_dict('''
        SELECT token_id, project_id, user_id, expires_at, revoked_at
        FROM secret_read_token
        WHERE token_id = %s AND token_hash = %s
    ''', [token_id, token_hash])

    if not row:
        abort(401, 'Invalid or unknown read-token.')

    if str(row['project_id']) != str(project_id):
        abort(403, 'Read-token is not valid for this project.')

    if str(row['user_id']) != str(g.token['user']['id']):
        abort(403, 'Read-token does not belong to the current user.')

    if row['revoked_at'] is not None:
        abort(401, 'Read-token has been revoked.')

    if row['expires_at'] < _utcnow_naive():
        abort(401, 'Read-token has expired. Apply for a new one.')

    # Track usage (best-effort; must not fail the read). Useful for auditing
    # who actually read plaintext secret values and when.
    try:
        g.db.execute(
            'UPDATE secret_read_token SET last_used_at = NOW() WHERE token_id = %s',
            [row['token_id']]
        )
        g.db.commit()
    except Exception:
        pass

    return row


@ns.route('/read-token')
@api.doc(responses={403: 'Not Authorized', 404: 'Project not found'})
class SecretReadToken(Resource):

    @api.response(201, 'Created', read_token_model)
    def post(self, project_id):
        '''
        Apply for a temporary read-token for this project's secret values.

        Restricted to project administrators by the OPA policy. The returned
        token is valid for 20 minutes and must be presented in the
        X-Secret-Read-Token header when reading decrypted values. The raw
        token is shown only once; only its hash is stored.
        '''
        if not validate_uuid(project_id):
            abort(400, 'Invalid project uuid.')

        project = g.db.execute_one_dict('''
            SELECT id FROM project WHERE id = %s
        ''', [project_id])

        if not project:
            abort(404, 'Project not found.')

        raw_suffix = secrets_lib.token_hex(24)  # 48 hex chars
        raw_token = _READ_TOKEN_PREFIX + raw_suffix
        token_id = raw_suffix[:16]
        token_hash = _hash_read_token(raw_token)

        # Compute expiry in Python as naive UTC so it shares the same clock as
        # the validation check (_utcnow_naive), independent of the DB session
        # timezone. Mirrors the mcp_token creation path.
        expires_at = _utcnow_naive() + timedelta(minutes=_READ_TOKEN_TTL_MINUTES)

        row = g.db.execute_one_dict('''
            INSERT INTO secret_read_token (token_id, token_hash, project_id, user_id, expires_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING expires_at
        ''', [token_id, token_hash, project_id, g.token['user']['id'], expires_at])
        g.db.commit()

        return {
            'token': raw_token,  # shown once only
            'expires_at': row['expires_at'].isoformat(),
        }, 201


@ns.route('/values')
@api.doc(responses={401: 'Read-token required/invalid/expired',
                    403: 'Not Authorized',
                    404: 'Project not found'})
class SecretValues(Resource):

    @api.marshal_list_with(secret_value_model)
    def get(self, project_id):
        '''
        Returns project's secrets with decrypted values.

        WARNING: this endpoint exposes plaintext secret values. Access requires
        BOTH project-administrator role (enforced by the OPA policy) AND a
        valid, unexpired temporary read-token in the X-Secret-Read-Token header
        (applied for via POST .../secrets/read-token).
        '''
        if not validate_uuid(project_id):
            abort(400, 'Invalid project uuid.')

        project = g.db.execute_one_dict('''
            SELECT id FROM project WHERE id = %s
        ''', [project_id])

        if not project:
            abort(404, 'Project not found.')

        _validate_read_token(project_id)

        secrets = g.db.execute_many_dict('''
            SELECT name, value FROM secret
            WHERE project_id = %s
        ''', [project_id])

        for secret in secrets:
            secret['value'] = decrypt_secret(secret['value'])

        return secrets
