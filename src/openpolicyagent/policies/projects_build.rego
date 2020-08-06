package infrabox

import input as api
import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects

build_collaborator([user, project]) {
    collaborators[i].project_id = project
    collaborators[i].user_id = user
}

build_project_public(project){
    projects[i].id = project
    projects[i].public = true
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, "restart"]
    api.token.type = "user"
    build_collaborator([api.token.user.id, project])
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, "restart"]
    api.token.type = "project"
    project = api.token.project.id
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, "abort"]
    api.token.type = "user"
    build_collaborator([api.token.user.id, project])
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, "abort"]
    api.token.type = "project"
    project = api.token.project.id
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
    api.path = ["api", "v1", "projects", project, "builds", _, _, "state"]
    api.token.type = "user"
    build_project_public(project)
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, _, "state"]
    api.token.type = "project"
    project = api.token.project.id
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, _]
    api.token.type = "user"
    build_collaborator([api.token.user.id, project])
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, _]
    build_project_public( project )
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds"]
    api.token.type = "project"
    api.token.project.id = project
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds"]
    build_project_public( project )
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _]
    api.token.type = "project"
    api.token.project.id = project
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "builds", _, "jobs"]
    api.token.type = "project"
    api.token.project.id = project
}