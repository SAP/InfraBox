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

# Allow GET access to /api/v1/projects/<project_id> for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id]

    api.token.type = "user"
    project_collaborator([api.token.user_id, project_id])
}

# Allow GET access to /api/v1/projects/<project_id> for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id]

    api.token.type = "project"
    api.token.project_id = project_id
}

# Allow GET access to /api/v1/projects/<project_id>/(state.svg|tests.svg|badges.svg) for collaborators
allow {
    svg_images := ["state.svg", "tests.svg", "badge.svg"]

    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, svg_image]
    svg_image = svg_images[_]

    api.token.type = "user"
    project_collaborator([api.token.user_id, project_id])
}

# Allow GET access to /api/v1/projects/<project_id>/(state.svg|tests.svg|badges.svg) if project is public
allow {
    svg_images := ["state.svg", "tests.svg", "badge.svg"]

    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, svg_image]
    svg_image = svg_images[_]

    project_public(project_id)
}

# Allow GET access to /api/v1/projects/<project_id>/(state.svg|tests.svg|badges.svg) for project tokens
allow {
    svg_images := ["state.svg", "tests.svg", "badge.svg"]

    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, svg_image]
    svg_image = svg_images[_]

    api.token.type = "project"
    api.token.project_id = project_id
}

# Allow POST access to /api/v1/projects/<project_id>/upload/<build_id>/ for project tokens
allow {
    api.method = "POST"
    api.path = ["api", "v1", "projects", project_id, "upload", _]

    api.token.type = "project"
    api.token.project_id = project_id
}