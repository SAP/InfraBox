package infrabox

import input as api

import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects
import data.infrabox.roles

projects_projects_owner([user, project]){
    collaborators[i].project_id = project
    collaborators[i].user_id = user
    roles[collaborators[i].role] >= 3
}

projects_projects_collaborator([user, project]) {
    collaborators[i].project_id = project
    collaborators[i].user_id = user
}

projects_projects_public(project){
    projects[i].id = project
    projects[i].public = true
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects"]
    api.token.type = "user"
}

allow {
    api.method = "POST"
    api.path = ["api", "v1", "projects",]
    api.token.type = "user"
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", "name", project_name]
    api.token.type = "user"
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project]
    api.token.type = "user"
    projects_projects_collaborator([api.token.user.id, project])
}
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project]
    projects_projects_public(project)
}

allow {
    api.method = "DELETE"
    api.path = ["api", "v1", "projects", project]
    api.token.type = "user"
    projects_projects_owner([api.token.user.id, project])
}


