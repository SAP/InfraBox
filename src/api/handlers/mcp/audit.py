"""
Audit logging for MCP API calls.

Writes to the mcp_access_log table (best-effort, synchronous).
Never raises — a logging failure must not break the request.

Uses its OWN short-lived autocommit connection, NOT the request's g.db and
NOT the shared eventlet pool (dbpool). This is deliberate:

  * Sharing g.db would let the audit commit end the caller's transaction —
    releasing any LOCK TABLE it holds and committing partially-written rows.
  * Borrowing a second connection from the pool (dbpool.get) would make the
    request hold TWO pooled connections at once (g.db + audit's). ibflask.py
    borrows g.db in before_request and only returns it in teardown_request,
    so it is held for the whole request. With max_size=10, N concurrent
    requests each also calling dbpool.get() here would deadlock permanently:
    all 10 connections are held as g.db, and every request blocks in the
    pool's channel.get() (which has NO timeout) waiting for an 11th that can
    never appear — the only greenlets that could free a connection are the
    ones stuck waiting. A private connection sidesteps the shared pool
    entirely and cannot participate in pool exhaustion.

connect_timeout bounds a slow/down DB so a best-effort log fails fast and is
swallowed, rather than hanging the request thread (as connect_db()'s unbounded
sleep(3) retry loop would). autocommit is safe here ONLY because the connection
is private and closed below — it is never returned to the pool, so it cannot
leak autocommit=True to a future borrower (eventlet's dbpool.put() rolls back
but does NOT reset session attributes like autocommit).
"""
import os
import json
import logging

import psycopg2

from flask import g, request

logger = logging.getLogger('mcp_audit')

# Bound how long we'll wait to open the audit connection. Best-effort logging
# must never make the caller wait; failures are swallowed below.
_AUDIT_CONNECT_TIMEOUT = 2


def audit_mcp(action: str, outcome: str = 'attempt', details: dict = None, error: str = ''):
    """Record one MCP audit entry on a dedicated autocommit connection.

    Never touches the request's g.db connection nor the shared dbpool, so it
    cannot commit/rollback the caller's transaction, cannot release a LOCK TABLE
    the caller holds, and cannot contribute to pool exhaustion/deadlock.
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
        # Private, short-lived connection built with the same parameters as
        # pyinfraboxutils.db.connect_db(), plus a bounded connect_timeout so a
        # down/slow DB fails fast instead of hanging the request.
        conn = psycopg2.connect(
            dbname=os.environ['INFRABOX_DATABASE_DB'],
            user=os.environ['INFRABOX_DATABASE_USER'],
            password=os.environ['INFRABOX_DATABASE_PASSWORD'],
            host=os.environ['INFRABOX_DATABASE_HOST'],
            port=os.environ['INFRABOX_DATABASE_PORT'],
            connect_timeout=_AUDIT_CONNECT_TIMEOUT,
        )
        conn.autocommit = True  # safe: this connection is private and closed below
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
        # Best-effort: never raise into the caller. A failed audit write must
        # not break the request it is auditing.
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
