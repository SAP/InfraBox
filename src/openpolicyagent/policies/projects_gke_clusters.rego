package infrabox

import input as api
import data.infrabox.collaborators.collaborators


# Any collaborator (Owner/Developer/Viewer) of the project may
# manage GKE clusters within it.  Fine-grained role gating can be added
# in v1 alongside audit + rate limiting.
gke_project_collaborator([user, project]) {
    collaborators[i].project_id = project
    collaborators[i].user_id = user
}


# POST /api/v1/projects/<pid>/gke-clusters       -> create
allow {
    api.method = "POST"
    api.path = ["api", "v1", "projects", project, "gke-clusters"]
    api.token.type = "user"
    gke_project_collaborator([api.token.user.id, project])
}

# GET /api/v1/projects/<pid>/gke-clusters/<name> -> read status
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "gke-clusters", _]
    api.token.type = "user"
    gke_project_collaborator([api.token.user.id, project])
}

# GET /api/v1/projects/<pid>/gke-clusters/<name>/kubeconfig -> read kubeconfig
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project, "gke-clusters", _, "kubeconfig"]
    api.token.type = "user"
    gke_project_collaborator([api.token.user.id, project])
}

# DELETE /api/v1/projects/<pid>/gke-clusters/<name> -> delete
allow {
    api.method = "DELETE"
    api.path = ["api", "v1", "projects", project, "gke-clusters", _]
    api.token.type = "user"
    gke_project_collaborator([api.token.user.id, project])
}