import json
import requests

from pyinfraboxutils import get_logger, get_env, dbpool


logger = get_logger('OPA')

def opa_push_data():
    db = dbpool.get()
    opa_push_collaborator_data(db)
    opa_push_project_data(db)



def opa_push_collaborator_data(db):
    collaborators = db.execute_many_dict(
        """
        SELECT user_id, project_id, role FROM collaborator
    """)
    payload = json.dumps({'collaborators': collaborators})
    try:
        rsp = requests.put(get_collaborator_data_destination(), data=payload, headers={"Content-Type" : "application/json"})
        if rsp:
            logger.debug("Pushed collaborator data to Open Policy Agent (Status %s):%s", str(rsp.status_code), payload)
        else:
            logger.error("Failed pushing collaborator data to Open Policy Agent (Status %s): Req.: %s; Resp.: %s", str(rsp.status_code), payload, rsp.content)
    except requests.exceptions.RequestException as e:
        logger.exception("Failed pushing collaborator data to Open Policy Agent: %s; Req.: %s", e, payload)



def opa_push_project_data(db):
    projects = db.execute_many_dict(
        """
        SELECT id, public FROM project
    """
    )
    payload = json.dumps({"projects": projects})

    try:
        rsp = requests.put(get_project_data_destination(), data=payload, headers={"Content-Type" : "application/json"})
        if rsp:
            logger.debug("Pushed project data to Open Policy Agent (Status %s):%s", str(rsp.status_code), payload)
        else:
            logger.error("Failed pushing project data to Open Policy Agent (Status %s): Req.: %s; Resp.: %s", str(rsp.status_code), payload, rsp.content)
    except requests.exceptions.RequestException as e:
        logger.exception("Failed pushing project data to Open Policy Agent: %s; Req.: %s", e, payload)

def get_collaborator_data_destination():
    return "%s/v1/data/infrabox/collaborators" % get_env("INFRABOX_OPA_HOST")

def get_project_data_destination():
    return "%s/v1/data/infrabox/projects" % get_env("INFRABOX_OPA_HOST")