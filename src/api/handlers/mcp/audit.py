"""
Audit logging for MCP API calls.

Writes to the mcp_access_log table (best-effort, synchronous).
Never raises — a logging failure must not break the request.

The audit write uses its OWN short-lived autocommit connection, NOT the
request's g.db connection. This is deliberate: sharing g.db would let the
audit commit end the caller's transaction — releasing any LOCK TABLE it
holds and committing partially-written (possibly orphan) rows. Isolating
the audit connection keeps the caller's transaction boundary intact.
"""
import json
import logging

from flask import g, request

from pyinfraboxutils.db import connect_db

logger = logging.getLogger('mcp_audit')


def audit_mcp(action: str, outcome: str = 'attempt', details: dict = None, error: str = ''):
    """Record one MCP audit entry on a dedicated autocommit connection.

    Never touches the request's g.db connection, so it cannot commit or roll
    back the caller's in-flight transaction, and cannot release a LOCK TABLE
    the caller holds.
    """
    token_id = getattr(g, 'mcp_token_id', None)
    user_id = getattr(g, 'mcp_token_user_id', None)
    if not user_id:
        token = getattr(g, 'token', None)
        if token and 'user' in token:
            user_id = str(token['user'].get('id', ''))
    ip = request.remote_addr

    conn = None
    try:
        conn = connect_db()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO mcp_access_log (token_id, user_id, action, outcome, details, error, ip)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', [
            token_id,
            user_id,
            action,
            outcome,
            _to_json(details),
            error or None,
            ip,
        ])
        cur.close()
    except Exception as exc:
        logger.warning('MCP audit log failed: %s', exc)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _to_json(d):
    if d is None:
        return None
    try:
        return json.dumps(d)
    except Exception:
        return str(d)

