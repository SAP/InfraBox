package infrabox

import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects

# HTTP API request
import input as http_api

project_owner[[user, project]]{
    project_collaborator[[user, project]][i]
    collaborators[i].role = "Owner"
}

project_collaborator[[user, project]]{
    user_projects[i] = project_collaborators[j]
}

user_projects[user]{
    user = collaborators[i].user_id
}

project_collaborators[project]{
    project = projects[_].id
    project = collaborators[_].project_id
}

allow {
    http_api.method = "DELETE"
    http_api.path = ["api", "v1", "projects", project]
    project_owner[[http_api.user, project]]
}