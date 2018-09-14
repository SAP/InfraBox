import json
import requests

from pyinfraboxutils import get_logger, get_env


logger = get_logger('OPA')
def opa_push_collaborator_data(db):
    collaborators = db.execute_many_dict(
        """
        SELECT user_id, project_id, role FROM collaborator
    """)
    payload = json.dumps({'collaborators': collaborators})
    requests.put(get_collaborator_data_destination(), data=payload, headers={"Content-Type" : "application/json"})
    logger.info("Pushed updated collaborator data to OpenPolicyAgent: " + payload)

def opa_push_project_data(db):
    projects = db.execute_many_dict(
        """
        SELECT id, public FROM project
    """
    )
    payload = json.dumps({"projects": projects})
    requests.put(get_project_data_destination(), data=payload, headers={"Content-Type" : "application/json"})
    logger.info("Pushed updated project data to OpenPolicyAgent: " + payload)

def get_collaborator_data_destination():
    return get_env("INFRABOX_OPA_HOST") + "/v1/data/infrabox/collaborators"

def get_project_data_destination():
    return get_env("INFRABOX_OPA_HOST") + "/v1/data/infrabox/projects"
