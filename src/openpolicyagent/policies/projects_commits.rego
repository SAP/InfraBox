package infrabox

import input as api

import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects

project_commits_collaborator([user, project_id]) {
    collaborators[i].project_id = project
    collaborators[i].user_id = user
}

project_commits_public(project){
    projects[i].id = project
    projects[i].public = true
}

# Allow GET /api/v1/projects/<id>/commits/<id> for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "commits", _]
    api.token.type = "user"
    project_commits_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<id>/commits/<id> if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "commits", _]
    project_commits_public(project_id)
}