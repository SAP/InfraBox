package infrabox

# HTTP API request
import input as api

u_id = user_id[api]

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", "re"]
    user_valid(token)
}

allow {
    api.method = "POST"
    api.path = ["api", "v1", "projects", "re"]
    user_valid(token)
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", "name", project_name]
    user_valid(token)
}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project]
    user_valid(token)
    project_collaborator([u_id, project])
}
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project]
    user_valid(token)
    project_public(project)
}

allow {
    api.method = "DELETE"
    api.path = ["api", "v1", "projects", project]
    user_valid(token)
    project_owner(u_id, project])
}

