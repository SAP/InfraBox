import time

from prometheus_client import Counter, Histogram, start_http_server

from pyinfraboxutils.ibflask import app

from flask import request

FLASK_REQUEST_LATENCY = Histogram('flask_request_latency_seconds', 'Flask Request Latency',
                                  ['method', 'endpoint'])
FLASK_REQUEST_COUNT = Counter('flask_request_count', 'Flask Request Count',
                              ['method', 'endpoint', 'http_status'])

def monitor(port):
    @app.before_request
    def _before_request():
        request.start_time = time.time()

    @app.after_request
    def _after_request(response):
        request_latency = time.time() - request.start_time
        #pylint: disable=no-member
        FLASK_REQUEST_LATENCY.labels(request.method, request.path).observe(request_latency)
        FLASK_REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
        return response

    start_http_server(port, '0.0.0.0')
