package infrabox

# HTTP API request
import input as http_api

u_id = user_id[http_api]

allow {
    http_api.method = "GET"
    http_api.path = ["api", "v1", "projects", "re"]
    user_valid(token)
}

allow {
    http_api.method = "POST"
    http_api.path = ["api", "v1", "projects", "re"]
    user_valid(token)
}

allow {
    http_api.method = "GET"
    http_api.path = ["api", "v1", "projects", "name", project_name]
    user_valid(token)
}

allow {
    http_api.method = "GET"
    http_api.path = ["api", "v1", "projects", project]
    user_valid(token)
    project_collaborator([u_id, project])
}
allow {
    http_api.method = "GET"
    http_api.path = ["api", "v1", "projects", project]
    user_valid(token)
    project_public(project)
}

allow {
    http_api.method = "DELETE"
    http_api.path = ["api", "v1", "projects", project]
    user_valid(token)
    project_owner(u_id, project])
}

