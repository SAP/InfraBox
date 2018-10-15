package infrabox

import input as api

import data.infrabox.projects.projects

# Allow GET access to /api/ping for all
allow {
    api.path = ["api", "ping"]
}

# Allow GET access to /ping for all
allow {
    api.path = ["ping"]
}

# Allow GET access to /api/status for all
allow {
    api.path = ["api", "status"]
}

# Allow access to /v2
allow {
    api.path = ["v2"]
    api.token.type = "project"
}

allow {
    api.path = ["v2"]
    api.token.type = "job"
    states := ["scheduled", "running"]
    api.token.job.state = states[_]
}

# Allow access to /v2/path
allow {
    api.original_method = "GET"
    api.path[0] = "v2"
    api.path[1] = project_id
    count(api.path, path_length)
    path_length >= 3

    api.token.type = "project"
    api.token.project.id = project_id
    project_id = projects[_].id
}

allow {
    api.original_method
    api.path[0] = "v2"
    api.path[1] = project_id
    count(api.path, path_length)
    path_length >= 3

    api.token.type = "job"
    states := ["scheduled", "running"]
    api.token.job.state = states[_]
    api.token.project.id = project_id
    project_id = projects[_].id
}
