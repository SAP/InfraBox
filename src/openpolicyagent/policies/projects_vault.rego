package infrabox

import input as api

import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects
import data.infrabox.roles

# Vault admins definition
projects_vault_administrator([user, project]){
    collaborators[i].project_id = project
    collaborators[i].user_id = user
    roles[collaborators[i].role] >= 20
}

# Project tokens definition
valid_project_token([token, project_id]) {
    token.type = "project"
    token.project.id = project_id
}

# Allow GET access to /api/v1/projects/<project_id>/vault for project administrators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "vault"]
    api.token.type = "user"
    projects_vault_administrator([api.token.user.id, project_id])
}
# Allow GET access to /api/v1/projects/<project_id>/vault for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "vault"]
    valid_project_token([api.token, project_id])
}

# Allow POST access to /api/v1/projects/<project_id>/vault for project administrators
allow {
    api.method = "POST"
    api.path = ["api", "v1", "projects", project_id, "vault"]
    api.token.type = "user"
    projects_vault_administrator([api.token.user.id, project_id])
}
# Allow POST access to /api/v1/projects/<project_id>/vault for valid project token
allow {
    api.method = "POST"
    api.path = ["api", "v1", "projects", project_id, "vault"]
    valid_project_token([api.token, project_id])
}

# Allow DELETE access to /api/v1/projects/<project_id>/vault/<vault_id> for project administrators
allow {
    api.method = "DELETE"
    api.path = ["api", "v1", "projects", project_id, "vault", vault_id]
    api.token.type = "user"
    projects_vault_administrator([api.token.user.id, project_id])
}
# Allow DELETE access to /api/v1/projects/<project_id>/vault/<vault_id> for valid project token
allow {
    api.method = "DELETE"
    api.path = ["api", "v1", "projects", project_id, "vault", vault_id]
    valid_project_token([api.token, project_id])
}