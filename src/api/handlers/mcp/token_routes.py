"""
MCP token management endpoints.
Authenticated by normal session/OPA auth (not MCP tokens).

POST   /api/v1/mcp/tokens              create
GET    /api/v1/mcp/tokens              list
PATCH  /api/v1/mcp/tokens/<id>         update
DELETE /api/v1/mcp/tokens/<id>         revoke
POST   /api/v1/mcp/tokens/<id>/trigger grant trigger permission (permanent until revoked)
DELETE /api/v1/mcp/tokens/<id>/trigger revoke trigger permission
"""
import json
import os
import secrets
from datetime import datetime, timezone, timedelta

from flask import g, request, abort
from flask_restx import Resource

from pyinfraboxutils.ibrestplus import api
from api.handlers.mcp.audit import audit_mcp
from api.handlers.mcp.auth import _hash_token

_MAX_EXPIRY_DAYS = int(os.environ.get('MCP_TOKEN_MAX_EXPIRY_DAYS', 365))
_MAX_PER_USER = int(os.environ.get('MCP_TOKEN_MAX_PER_USER', 20))

ns = api.namespace('MCP Tokens',
                   path='/api/v1/mcp/tokens',
                   description='MCP token management (session auth required)')


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _current_user_id():
    token = getattr(g, 'token', None)
    if not token or 'user' not in token:
        abort(401, 'authentication required')
    return str(token['user']['id'])


def _own_token(token_id, user_id):
    return g.db.execute_one_dict('''
        SELECT token_id, name, enabled_projects, allow_trigger, expires_at, revoked_at, created_at, last_used_at
        FROM mcp_token
        WHERE token_id = %s AND user_id = %s AND revoked_at IS NULL
    ''', [token_id, user_id])


@ns.route('/')
class MCPTokenList(Resource):
    def get(self):
        """List all active MCP tokens for the current user."""
        user_id = _current_user_id()
        rows = g.db.execute_many_dict('''
            SELECT token_id, name, enabled_projects, allow_trigger, expires_at, created_at, last_used_at
            FROM mcp_token
            WHERE user_id = %s AND revoked_at IS NULL
            ORDER BY created_at DESC
        ''', [user_id])
        return [_serialize(r) for r in rows]

    def post(self):
        """Create a new MCP token."""
        user_id = _current_user_id()

        count = g.db.execute_one('''
            SELECT COUNT(*) FROM mcp_token WHERE user_id = %s AND revoked_at IS NULL
        ''', [user_id])[0]
        if count >= _MAX_PER_USER:
            return {'message': f'max {_MAX_PER_USER} tokens per user', 'status': 400}, 400

        body = request.get_json(silent=True) or {}
        name = (body.get('name') or '').strip()[:128]
        if not name:
            return {'message': 'name is required', 'status': 400}, 400

        enabled_projects = body.get('enabled_projects') or {}
        if not isinstance(enabled_projects, dict):
            return {'message': 'enabled_projects must be an object', 'status': 400}, 400

        expires_days = int(body.get('expires_days') or _MAX_EXPIRY_DAYS)
        if expires_days < 1 or expires_days > _MAX_EXPIRY_DAYS:
            return {'message': f'expires_days must be 1–{_MAX_EXPIRY_DAYS}', 'status': 400}, 400

        expires_at = _utcnow() + timedelta(days=expires_days)

        raw_suffix = secrets.token_hex(24)  # 48 hex chars
        raw_token = f'ib_mcp_{raw_suffix}'
        token_id = raw_suffix[:16]
        token_hash = _hash_token(raw_token)

        g.db.execute('''
            INSERT INTO mcp_token (token_id, token_hash, user_id, name, enabled_projects, allow_trigger, expires_at)
            VALUES (%s, %s, %s, %s, %s, FALSE, %s)
        ''', [token_id, token_hash, user_id, name, json.dumps(enabled_projects), expires_at])
        g.db.commit()

        audit_mcp('create_mcp_token', outcome='success', details={'token_id': token_id, 'name': name})

        return {
            'token_id': token_id,
            'token': raw_token,  # shown once only
            'name': name,
            'enabled_projects': enabled_projects,
            'allow_trigger': False,
            'expires_at': expires_at.isoformat(),
        }, 201


@ns.route('/<string:token_id>')
class MCPToken(Resource):
    def patch(self, token_id):
        """Update a token's name, enabled_projects, or expires_at."""
        user_id = _current_user_id()
        row = _own_token(token_id, user_id)
        if not row:
            abort(404)

        body = request.get_json(silent=True) or {}

        updates = []
        params = []

        if 'name' in body:
            name = str(body['name']).strip()[:128]
            updates.append('name = %s')
            params.append(name)

        if 'enabled_projects' in body:
            if not isinstance(body['enabled_projects'], dict):
                return {'message': 'enabled_projects must be an object', 'status': 400}, 400
            updates.append('enabled_projects = %s')
            params.append(json.dumps(body['enabled_projects']))

        if 'expires_days' in body:
            try:
                days = int(body['expires_days'])
            except (ValueError, TypeError):
                return {'message': 'expires_days must be an integer', 'status': 400}, 400
            if days < 1 or days > _MAX_EXPIRY_DAYS:
                return {'message': f'expires_days must be 1–{_MAX_EXPIRY_DAYS}', 'status': 400}, 400
            updates.append('expires_at = %s')
            params.append(_utcnow() + timedelta(days=days))

        if not updates:
            return {'message': 'nothing to update', 'status': 400}, 400

        params.append(token_id)
        params.append(user_id)
        g.db.execute(
            f'UPDATE mcp_token SET {", ".join(updates)} WHERE token_id = %s AND user_id = %s',
            params
        )
        g.db.commit()
        audit_mcp('update_mcp_token', outcome='success', details={'token_id': token_id})
        return {'message': 'token updated', 'status': 200}

    def delete(self, token_id):
        """Revoke a token (soft delete)."""
        user_id = _current_user_id()
        row = _own_token(token_id, user_id)
        if not row:
            abort(404)

        g.db.execute(
            'UPDATE mcp_token SET revoked_at = NOW() WHERE token_id = %s AND user_id = %s',
            [token_id, user_id]
        )
        g.db.commit()
        audit_mcp('revoke_mcp_token', outcome='success', details={'token_id': token_id})
        return {'message': 'token revoked', 'status': 200}


@ns.route('/<string:token_id>/trigger')
class MCPTokenTrigger(Resource):
    def post(self, token_id):
        """Grant trigger permission to a token (permanent until revoked via DELETE)."""
        user_id = _current_user_id()
        row = _own_token(token_id, user_id)
        if not row:
            abort(404)

        g.db.execute(
            'UPDATE mcp_token SET allow_trigger = TRUE WHERE token_id = %s AND user_id = %s',
            [token_id, user_id]
        )
        g.db.commit()
        audit_mcp('grant_mcp_trigger', outcome='success', details={'token_id': token_id})
        return {'message': 'trigger permission granted', 'status': 200}

    def delete(self, token_id):
        """Revoke trigger permission from a token."""
        user_id = _current_user_id()
        row = _own_token(token_id, user_id)
        if not row:
            abort(404)

        g.db.execute(
            'UPDATE mcp_token SET allow_trigger = FALSE WHERE token_id = %s AND user_id = %s',
            [token_id, user_id]
        )
        g.db.commit()
        audit_mcp('revoke_mcp_trigger', outcome='success', details={'token_id': token_id})
        return {'message': 'trigger permission revoked', 'status': 200}


def _serialize(row):
    return {
        'token_id': row['token_id'],
        'name': row['name'],
        'enabled_projects': row['enabled_projects'],
        'allow_trigger': row['allow_trigger'],
        'expires_at': row['expires_at'].isoformat() if row['expires_at'] else None,
        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
        'last_used_at': row['last_used_at'].isoformat() if row.get('last_used_at') else None,
    }
