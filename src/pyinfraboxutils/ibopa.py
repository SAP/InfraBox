import json
import requests

import threading
import time

from pyinfraboxutils import get_logger, get_env
from pyinfraboxutils import dbpool

logger = get_logger('OPA')

OPA_AUTH_URL = "http://%s:%s/v1/data/infrabox/authz" % (get_env('INFRABOX_OPA_HOST'), get_env('INFRABOX_OPA_PORT'))
COLLABORATOR_DATA_DEST_URL = "http://%s:%s/v1/data/infrabox/collaborators" % (get_env('INFRABOX_OPA_HOST'), get_env('INFRABOX_OPA_PORT'))
PROJECT_DATA_DEST_URL = "http://%s:%s/v1/data/infrabox/projects" % (get_env('INFRABOX_OPA_HOST'), get_env('INFRABOX_OPA_PORT'))

exit_flag = 0

def opa_do_auth(input_dict):
    # Send request to Open Policy Agent and evaluate response
    payload = json.dumps(input_dict)
    logger.debug("Sending OPA Request: %s", payload)
    rsp = requests.post(OPA_AUTH_URL, data=json.dumps(input_dict))
    rsp_dict = rsp.json()
    logger.debug("OPA Response: %s", rsp.content)

    return "result" in rsp_dict and rsp_dict["result"] is True

def opa_push_data(destination_url, json_payload):
    try:
        rsp = requests.put(destination_url, data=json_payload, headers={"Content-Type" : "application/json"})
        if rsp:
            logger.debug("Pushed data to %s (Status %s):%s", destination_url, str(rsp.status_code), json_payload)
        else:
            logger.error("Failed pushing data to %s (Status %s): Req.: %s; Resp.: %s",
                         destination_url, str(rsp.status_code), json_payload, rsp.content)
    except requests.exceptions.RequestException as e:
        logger.exception("Failed pushing data to %s: %s; Req.: %s", destination_url, e, json_payload)

def opa_push_collaborator_data(db):
    collaborators = db.execute_many_dict("""
        SELECT user_id, project_id, role FROM collaborator
    """)
    payload = json.dumps({'collaborators': collaborators}, indent=4)
    opa_push_data(COLLABORATOR_DATA_DEST_URL, payload)

def opa_push_project_data(db):
    projects = db.execute_many_dict("""
        SELECT id, public, name FROM project
    """
    )
    payload = json.dumps({"projects": projects}, indent=4)
    opa_push_data(PROJECT_DATA_DEST_URL, payload)

def opa_push_all():
    db = dbpool.get()

    try:
        opa_push_collaborator_data(db)
        opa_push_project_data(db)
    finally:
        dbpool.put(db)

def opa_start_push_loop():
    class OPA_Push_Thread(threading.Thread):
        stopped = False
        push_interval = float(get_env('INFRABOX_OPA_PUSH_INTERVAL'))
        def run(self):
            while not self.stopped:
                try:
                    opa_push_all()
                except Exception as e:
                    logger.exception(e)
                finally:
                    time.sleep(self.push_interval)

        def join(self, timeout=None):
            self.stopped = True
            threading.Thread.join(self, timeout)

    thread = OPA_Push_Thread()
    thread.daemon = True
    thread.start()
