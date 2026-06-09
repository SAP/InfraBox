"""
MCP token authentication middleware for InfraBox.

Token format: ib_mcp_<48 hex chars>
Lookup key:   first 16 chars of the 48-char hex suffix
Hash:         SHA-256 of the full raw token string (UTF-8)

MCP tokens are ONLY accepted on /api/v1/mcp/* paths.
All other paths fall back to the normal OPA-based auth.
"""
import hashlib
import logging
from datetime import datetime, timezone
from functools import wraps

from flask import g, request, jsonify

logger = logging.getLogger('mcp_auth')

_MCP_TOKEN_PREFIX = 'ib_mcp_'
_MCP_PATH_PREFIX = '/api/v1/mcp/'


def _utcnow():
    return datetime.now(timezone.utc)


def _utcnow_naive():
    """Naive UTC datetime for comparing against psycopg2 TIMESTAMP values."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def _reject(status, message):
    return jsonify({'message': message, 'status': status}), status


def mcp_auth_required(f):
    """Decorator that validates ib_mcp_* Bearer tokens.

    Sets on flask.g:
      g.mcp_token_id          – token_id (16-char prefix)
      g.mcp_token_user_id     – user uuid who owns the token
      g.mcp_enabled_projects  – dict {project_id: expires_at_iso_or_None}
      g.mcp_allow_trigger     – bool
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')

        if not auth.startswith('Bearer ' + _MCP_TOKEN_PREFIX):
            # not an MCP token — fall through to OPA auth (already done in before_request)
            return f(*args, **kwargs)

        raw_token = auth[len('Bearer '):]

        # MCP tokens are only valid on /api/v1/mcp/* paths
        if not request.path.startswith(_MCP_PATH_PREFIX):
            return _reject(403, 'MCP token can only be used on /api/v1/mcp/* endpoints')

        token_suffix = raw_token[len(_MCP_TOKEN_PREFIX):]
        if len(token_suffix) != 48:
            return _reject(401, 'invalid MCP token format')

        token_id = token_suffix[:16]
        token_hash = _hash_token(raw_token)

        row = g.db.execute_one_dict('''
            SELECT token_id, user_id, enabled_projects, allow_trigger, expires_at, revoked_at
            FROM mcp_token
            WHERE token_id = %s AND token_hash = %s
        ''', [token_id, token_hash])

        if not row:
            return _reject(401, 'invalid or unknown MCP token')

        if row['revoked_at'] is not None:
            return _reject(401, 'MCP token has been revoked')

        if row['expires_at'] < _utcnow_naive():
            return _reject(401, 'MCP token has expired')

        # Update last_used_at (best-effort, non-fatal)
        try:
            g.db.execute(
                'UPDATE mcp_token SET last_used_at = NOW() WHERE token_id = %s',
                [token_id]
            )
            g.db.commit()
        except Exception as exc:
            logger.warning('failed to update last_used_at: %s', exc)

        g.mcp_token_id = token_id
        g.mcp_token_user_id = str(row['user_id'])
        g.mcp_enabled_projects = row['enabled_projects'] or {}
        g.mcp_allow_trigger = bool(row['allow_trigger'])
        # Suppress OPA check for MCP-authed requests
        g.token = {'type': 'mcp', 'user': {'id': str(row['user_id']), 'role': 'user'}}

        return f(*args, **kwargs)
    return decorated


def check_project_access_mcp(project_id: str) -> bool:
    """Return True if the current request may access project_id.

    MCP token path: project must be in g.mcp_enabled_projects and not past
    its per-project expiry (if set).
    Session path: delegates to OPA (already checked in before_request).
    """
    if not hasattr(g, 'mcp_enabled_projects'):
        # session / OPA path — access already verified
        return True

    enabled = g.mcp_enabled_projects
    if project_id not in enabled:
        return False

    per_project_expiry = enabled[project_id]
    if per_project_expiry:
        try:
            exp = datetime.fromisoformat(per_project_expiry)
            # fromisoformat() on a naive string (no UTC offset) returns a naive
            # datetime; compare against naive UTC to avoid TypeError.
            now = _utcnow_naive() if exp.tzinfo is None else _utcnow()
            if exp < now:
                return False
        except (ValueError, TypeError):
            # Malformed expiry — treat as expired rather than silently granting access.
            return False

    return True


def check_trigger_access_mcp() -> bool:
    """Return True if the current request may trigger builds."""
    if not hasattr(g, 'mcp_allow_trigger'):
        return True
    return bool(g.mcp_allow_trigger)


def get_mcp_user_id() -> str:
    """Return user id string regardless of auth path."""
    if hasattr(g, 'mcp_token_user_id'):
        return g.mcp_token_user_id
    token = getattr(g, 'token', None)
    if token and 'user' in token:
        return str(token['user'].get('id', ''))
    return request.remote_addr or 'unknown'
