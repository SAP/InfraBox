"""
Audit logging for MCP API calls.

Writes to the mcp_access_log table (best-effort, synchronous) on the
request's g.db connection.

Never raises — a logging failure must not break the request.

IMPORTANT invariants for callers (this audit shares g.db and commits it):
  * Call audit('attempt')/('forbidden') BEFORE any write in the handler —
    audit's commit() would otherwise flush uncommitted work.
  * Call audit('success') only AFTER the handler's own g.db.commit().
  * On any failure path that has already executed SQL (a failed statement
    poisons the connection, or an uncommitted write is pending), call
    g.db.rollback() BEFORE audit('failure') — otherwise the audit INSERT
    either fails on the aborted connection (losing the log) or commits a
    stray partial write.
  * Never call audit inside a LOCK TABLE / SELECT ... FOR UPDATE critical
    section — its commit() would release the lock mid-transaction.
"""
import json
import logging

from flask import g, request

logger = logging.getLogger('mcp_audit')


def audit_mcp(action: str, outcome: str = 'attempt', details: dict = None, error: str = ''):
    """Record one MCP audit entry synchronously on the request DB connection."""
    token_id = getattr(g, 'mcp_token_id', None)
    user_id = getattr(g, 'mcp_token_user_id', None)
    if not user_id:
        token = getattr(g, 'token', None)
        if token and 'user' in token:
            user_id = str(token['user'].get('id', ''))
    ip = request.remote_addr

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
    try:
        return json.dumps(d)
    except Exception:
        return str(d)
