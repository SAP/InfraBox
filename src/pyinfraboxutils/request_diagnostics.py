"""Trace job bootstrap requests without logging tokens or response payloads."""
import os
import time
import uuid
from contextlib import contextmanager
from functools import wraps

from flask import g, has_request_context, request

from pyinfraboxutils import get_logger

logger = get_logger(__name__)


def start_job_request():
    if request.method != 'GET' or request.path != '/api/job/job':
        return

    try:
        request_id = str(uuid.UUID(request.headers.get('X-Request-ID', '')))
    except ValueError:
        request_id = str(uuid.uuid4())

    g.job_request_diagnostics = {
        'request_id': request_id,
        'started': time.monotonic(),
    }
    logger.warning('Job data request started: request_id=%s method=%s path=%s worker=%s',
                   request_id, request.method, request.path, os.getpid())


@contextmanager
def request_stage(stage):
    trace = getattr(g, 'job_request_diagnostics', None) if has_request_context() else None
    if trace is None:
        yield
        return

    started = time.monotonic()
    job_id = (getattr(g, 'token', None) or {}).get('job', {}).get('id', 'unknown')
    logger.warning('Job data stage started: request_id=%s job_id=%s stage=%s',
                   trace['request_id'], job_id, stage)
    try:
        yield
    except Exception:
        logger.exception('Job data stage failed: request_id=%s job_id=%s stage=%s elapsed=%.2fs',
                         trace['request_id'], job_id, stage, time.monotonic() - started)
        raise
    else:
        logger.warning('Job data stage completed: request_id=%s job_id=%s stage=%s elapsed=%.2fs',
                       trace['request_id'], job_id, stage, time.monotonic() - started)


def trace_call(stage, function, *args, **kwargs):
    with request_stage(stage):
        return function(*args, **kwargs)


def trace_stage(stage):
    def decorate(function):
        @wraps(function)
        def traced(*args, **kwargs):
            with request_stage(stage):
                return function(*args, **kwargs)
        return traced
    return decorate


def finish_job_request(response):
    trace = getattr(g, 'job_request_diagnostics', None)
    if trace is not None:
        response.headers['X-Request-ID'] = trace['request_id']
        logger.warning('Job data request completed: request_id=%s status=%s elapsed=%.2fs',
                       trace['request_id'], response.status_code,
                       time.monotonic() - trace['started'])
    return response
