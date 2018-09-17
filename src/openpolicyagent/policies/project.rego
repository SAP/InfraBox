package infrabox

import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects

# HTTP API request
import input as http_api

project_owner[[user, project]]{
    collaborators[i].project_id = project
    collaborators[i].user_id = user
    collaborators[i].role = "Owner"
}

project_collaborator[[user, project]]{
    collaborators[i].project_id = project
    collaborators[i].user_id = user
}

allow {
    http_api.method = "DELETE"
    http_api.path = ["api", "v1", "projects", project]
    project_owner[[http_api.user, project]]
}