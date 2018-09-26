package infrabox

import input as api

import data.infrabox.projects.projects

# Allow GET access to /ping for all
allow {
    api.path = ["ping"]
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
    api.path = ["v2", project_id]
    count(project_id, project_id_length)
    project_id_length >= 2

    api.token.type = "project"
    api.token.project.id = project_id
    project_id = projects[_].id
}

allow {
    api.original_method
    api.path = ["v2", project_id]
    count(project_id, project_id_length)
    project_id_length >= 2

    api.token.type = "job"
    states := ["scheduled", "running"]
    api.token.job.state = states[_]
    api.token.project.id = project_id
    project_id = projects[_].id
}