from flask import g, jsonify

from pyinfraboxutils import get_env, get_logger
from pyinfraboxutils.ibflask import app

logger = get_logger('state')

@app.route('/')
def state():
    r = g.db.execute_many_dict('''
        SELECT * FROM cluster
    ''')

    return jsonify(r)

def main(): # pragma: no cover
    get_env('INFRABOX_VERSION')
    get_env('INFRABOX_DATABASE_HOST')
    get_env('INFRABOX_DATABASE_USER')
    get_env('INFRABOX_DATABASE_PASSWORD')
    get_env('INFRABOX_DATABASE_PORT')
    get_env('INFRABOX_DATABASE_DB')

    from gevent.wsgi import WSGIServer
    http_server = WSGIServer(('', 8080), app, log=logger)
    http_server.serve_forever()

if __name__ == "__main__": # pragma: no cover
    main()
