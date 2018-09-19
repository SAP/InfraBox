package infrabox

import input as api

import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects
import data.infrabox.roles

socketio_project_collaborator([user, project]) {
    collaborators[i].project_id = project
    collaborators[i].user_id = user
}

socketio_project_public(project){
    projects[i].id = project
    projects[i].public = true
}

# Allow access to listen:jobs if project is public
allow {
    api.method = "WS"
    api.path = ["listen:jobs", project_id]
    api.token.type = "user"
    socketio_project_public(project_id)
}

# Allow access to listen:jobs if user is a project collaborator
allow {
    api.method = "WS"
    api.path = ["listen:jobs", project_id]
    api.token.type = "user"
    socketio_project_collaborator([api.token.user.id, project_id])
}

# Allow access to listen:build with valid project token
allow {
    api.method = "WS"
    api.path = ["listen:build", _]
    api.token.type = "project"
    projects[_].id = api.token.project.id
}

# Allow access to listen:console with valid project token
allow {
    api.method = "WS"
    api.path = ["listen:console", _]
    api.token.type = "project"
    projects[_].id = api.token.project.id
}

# Allow access to listen:dashboard-console if project is public
allow {
    api.method = "WS"
    api.path = ["listen:dashboard-console", project_id, _]
    api.token.type = "user"
    socketio_project_public(project_id)
}

# Allow access to listen:dashboard-console if user is a project collaborator
allow {
    api.method = "WS"
    api.path = ["listen:dashboard-console", project_id, _]
    api.token.type = "user"
    socketio_project_collaborator([api.token.user.id, project_id])
}