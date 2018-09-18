package infrabox

import input as api
import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects

build_collaborator([user, project]) {
    collaborators[i].project_id = project
    collaborators[i].user_id = user
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, "restart"]
    api.token.type = "user"
    build_collaborator([api.token.user.id, project])
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, "abort"]
    api.token.type = "user"
    build_collaborator([api.token.user.id, project])
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, "cache", "clear"]
    api.token.type = "user"
    build_collaborator([api.token.user.id, project])
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, _, "state"]
    api.token.type = "user"
    build_collaborator([api.token.user.id, project])
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, _]
    api.token.type = "user"
    build_collaborator([api.token.user.id, project])
}