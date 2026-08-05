"""
Pagination helpers for MCP list endpoints.

Every MCP list endpoint returns a bounded page by default so a single call can
never overflow the client/model context or hang on very large result sets.

Usage in a handler:

    from api.handlers.mcp.pagination import parse_pagination, page

    limit, offset = parse_pagination()          # reads ?limit=&offset=, validates
    ...run query with LIMIT %s OFFSET %s and a COUNT(*)...
    return page(items, total, limit, offset)

Callers that need the *entire* set page through by increasing offset until
offset + len(items) >= total.
"""
from flask import request, abort

DEFAULT_LIMIT = 50
MAX_LIMIT = 500


def parse_pagination():
    """Read and validate limit/offset from the query string.

    Returns (limit, offset). Missing params fall back to defaults, so an
    endpoint always applies a bound even when the caller passes nothing.
    Invalid values abort with 400.
    """
    limit = _parse_int('limit', DEFAULT_LIMIT)
    offset = _parse_int('offset', 0)

    if limit < 1:
        abort(400, 'limit must be >= 1')
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
    if offset < 0:
        abort(400, 'offset must be >= 0')

    return limit, offset


def _parse_int(name, default):
    raw = request.args.get(name)
    if raw is None or raw == '':
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        abort(400, '%s must be an integer' % name)


def page(items, total, limit, offset):
    """Wrap a page of items in the standard pagination envelope."""
    return {
        'items': items,
        'total': total,
        'limit': limit,
        'offset': offset,
    }
