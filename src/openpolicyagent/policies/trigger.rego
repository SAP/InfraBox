package infrabox

import input as api

import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects
import data.infrabox.roles

trigger_collaborator([user, project_id]) {
    collaborators[i].project_id = project
    collaborators[i].user_id = user
}

allow {
    api.method = "POST"
    api.path = ["api", "v1", "projects", project_id, "trigger"]
    api.token.type = "user"
    trigger_collaborator([api.token.user.id, project_id])
}
allow {
    api.method = "POST"
    api.path = ["api", "v1", "projects", project_id, "trigger"]
    api.token.type = "project"
    api.token.project.id = project_id
}

