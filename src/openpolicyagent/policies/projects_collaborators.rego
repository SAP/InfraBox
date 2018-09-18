package infrabox

import input as api
import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects
import data.infrabox.roles

collaborators_collaborator([user, project]) {
    collaborators[i].project_id = project
    collaborators[i].user_id = user
}

collaborators_owner([user, project]) {
    collaborators[i].project_id = project
    collaborators[i].user_id = user
    roles[collaborators[i].role] >=3
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "collaborators"]
    api.token.type = "user"
    collaborators_collaborator([api.token.user_id, project])
}

allow {
    api.method = "POST"
    api.path = ["api", "v1", "projects", project, "collaborators"]
    api.token.type = "user"
    collaborators_owner([api.token.user_id, project])
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "collaborators", "roles"]
    api.token.type = "user"
    collaborators_collaborator([api.token.user_id, project])
}

allow {
    api.method = "PUT"
    api.path = ["api", "v1", "projects", project, "collaborators", uuid_user]
    api.token.type = "user"
    collaborators_owner([api.token.user_id, project])
}

allow {
    api.method = "DELETE"
    api.path = ["api", "v1", "projects", project, "collaborators", uuid_user]
    api.token.type = "user"
    collaborators_owner([api.token.user_id, project])
}