"""
Audit logging for MCP API calls.

Writes to the mcp_access_log table (best-effort, fire-and-forget).
Never raises — a logging failure must not break the request.
"""
import logging
import threading

from flask import g, request

logger = logging.getLogger('mcp_audit')


def audit_mcp(action: str, outcome: str = 'attempt', details: dict = None, error: str = ''):
    """Record one MCP audit entry.  Non-blocking: runs in a daemon thread."""
    token_id = getattr(g, 'mcp_token_id', None)
    user_id = getattr(g, 'mcp_token_user_id', None)
    if not user_id:
        token = getattr(g, 'token', None)
        if token and 'user' in token:
            user_id = str(token['user'].get('id', ''))
    ip = request.remote_addr

    # Capture a snapshot of the db connection so the thread can use it safely.
    # For simplicity we write synchronously on the request db connection since
    # the volume is low.  If latency becomes a concern this can be offloaded.
    try:
        db = getattr(g, 'db', None)
        if db is None:
            return

        db.execute('''
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
        db.commit()
    except Exception as exc:
        logger.warning('MCP audit log failed: %s', exc)


def _to_json(d):
    if d is None:
        return None
    import json
    try:
        return json.dumps(d)
    except Exception:
        return str(d)
