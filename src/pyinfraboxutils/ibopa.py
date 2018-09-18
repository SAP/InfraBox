import json
import requests

from pyinfraboxutils import get_logger, get_env, dbpool

logger = get_logger('OPA')

OPA_AUTH_URL = "%s/v1/data/infrabox/allow" % get_env('INFRABOX_OPA_HOST')
COLLABORATOR_DATA_DEST_URL = "%s/v1/data/infrabox/collaborators" % get_env("INFRABOX_OPA_HOST")
PROJECT_DATA_DEST_URL = "%s/v1/data/infrabox/projects" % get_env("INFRABOX_OPA_HOST")

def opa_do_auth(input_dict):
    # Send request to Open Policy Agent and evaluate response
    payload = json.dumps(input_dict)
    logger.debug("Sending OPA Request: %s", payload)
    try:
        rsp = requests.post(OPA_AUTH_URL, data=json.dumps(input_dict))
        rsp_dict = rsp.json()
        logger.debug("OPA Response: %s", rsp.content)

        return "result" in rsp_dict and rsp_dict["result"] is True

    except requests.exceptions.RequestException as e:
        raise e

def opa_push_data(destination_url, json_payload):
    try:
        rsp = requests.put(destination_url, data=json_payload, headers={"Content-Type" : "application/json"})
        if rsp:
            logger.debug("Pushed data to %s (Status %s):%s", destination_url, str(rsp.status_code), json_payload)
        else:
            logger.error("Failed pushing data to %s (Status %s): Req.: %s; Resp.: %s", destination_url, str(rsp.status_code), json_payload, rsp.content)
    except requests.exceptions.RequestException as e:
        logger.exception("Failed pushing data to %s: %s; Req.: %s", destination_url, e, json_payload) 

def opa_push_collaborator_data(db):
    collaborators = db.execute_many_dict(
        """
        SELECT user_id, project_id, role FROM collaborator
    """)
    payload = json.dumps({'collaborators': collaborators})
    opa_push_data(COLLABORATOR_DATA_DEST_URL, payload)

def opa_push_project_data(db):
    projects = db.execute_many_dict(
        """
        SELECT id, public FROM project
    """
    )
    payload = json.dumps({"projects": projects})
    opa_push_data(PROJECT_DATA_DEST_URL, payload)

def opa_push_all():
    db = dbpool.get()
    opa_push_collaborator_data(db)
    opa_push_project_data(db)