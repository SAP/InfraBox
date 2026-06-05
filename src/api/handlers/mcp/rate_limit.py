"""
Redis sliding-window rate limiter for MCP endpoints.

Key:    ib_mcp_rl:{user_id}:{endpoint}
Window: 60 seconds
TTL:    70 seconds (slightly larger than window)

Fail-open: if Redis is unavailable, the request is allowed and a warning is logged.
"""
import logging
import os
import uuid
from functools import wraps

from flask import g, jsonify, request

logger = logging.getLogger('mcp_rate_limit')

_WINDOW_MS = 60_000
_KEY_TTL_S = 70

_ENDPOINT_LIMITS = {
    'get_job_log': int(os.environ.get('MCP_RATE_LIMIT_LOG_RPM', 10)),
    'list_job_artifacts': int(os.environ.get('MCP_RATE_LIMIT_ARTIFACT_RPM', 10)),
    'list_builds': int(os.environ.get('MCP_RATE_LIMIT_BUILDS_RPM', 30)),
    'list_jobs': int(os.environ.get('MCP_RATE_LIMIT_JOBS_RPM', 30)),
    'list_projects': int(os.environ.get('MCP_RATE_LIMIT_PROJECTS_RPM', 30)),
    'trigger_build': int(os.environ.get('MCP_RATE_LIMIT_TRIGGER_RPM', 5)),
}
_DEFAULT_RPM = int(os.environ.get('MCP_RATE_LIMIT_DEFAULT_RPM', 30))

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    redis_url = os.environ.get('REDIS_URL', '')
    if not redis_url:
        return None

    try:
        import redis
        _redis_client = redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)
        _redis_client.ping()
    except Exception as exc:
        logger.warning('MCP rate limiter: Redis unavailable (%s), fail-open', exc)
        _redis_client = None

    return _redis_client


def _check_rate_limit(user_id: str, endpoint: str) -> bool:
    """Return True (allow) or False (deny). Fail-open on Redis errors."""
    rpm = _ENDPOINT_LIMITS.get(endpoint, _DEFAULT_RPM)

    try:
        r = _get_redis()
        if r is None:
            return True

        import time
        now_ms = int(time.time() * 1000)
        key = f'ib_mcp_rl:{user_id}:{endpoint}'

        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, now_ms - _WINDOW_MS)
        pipe.zadd(key, {str(uuid.uuid4()): now_ms})
        pipe.zcard(key)
        pipe.expire(key, _KEY_TTL_S)
        results = pipe.execute()

        count = results[2]
        return count <= rpm

    except Exception as exc:
        logger.warning('MCP rate limiter Redis error (fail-open): %s', exc)
        return True


def mcp_rate_limit(endpoint: str):
    """Decorator factory: apply rate limiting for the given endpoint name."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from api.handlers.mcp.auth import get_mcp_user_id
            user_id = get_mcp_user_id()

            if not _check_rate_limit(user_id, endpoint):
                return jsonify({
                    'message': 'rate limit exceeded, please slow down',
                    'status': 429,
                }), 429

            return f(*args, **kwargs)
        return decorated
    return decorator
