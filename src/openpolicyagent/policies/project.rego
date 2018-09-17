package infrabox

import input as api

import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects
import data.infrabox.roles

project_owner([user, project]){
    collaborators[i].project_id = project
    collaborators[i].user_id = user
    roles[collaborators[i].role] >= 3
}

project_collaborator([user, project]) {
    collaborators[i].project_id = project
    collaborators[i].user_id = user
}

project_public(project){
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
    project_collaborator([api.token.user_id, project])
}
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project]
    api.token.type = "user"
    project_public(project)
}

allow {
    api.method = "DELETE"
    api.path = ["api", "v1", "projects", project]
    api.token.type = "user"
    project_owner([api.token.user_id, project])
}


