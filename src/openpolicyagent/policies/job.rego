package infrabox

# HTTP API request
import input as api

# job.py


job_state = {"queued", "running", "scheduled"}

# Allow GET access to api/v1/projects/<project_id>/jobs/<job_id> for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET access to api/v1/projects/<project_id>/jobs/<job_id>/output for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "output"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET access to api/v1/projects/<project_id>/jobs/<job_id>/manifest for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "manifest"]
    api.token.type = "project"
    api.token.project.id = project_id
}


# job_api.py

# Allow GET access to /api/job/* for valid job tokens
allow {
    api.method = "GET"
    api.path = ["api", "job", suffix]
    job_suffix := {"job", "source", "cache"}
    suffix = job_suffix[_]
    api.token.type = "job"
    api.token.job.state = job_state[_]
}

# Allow GET access to /api/job/output/<parent_job> for valid job tokens
allow {
    api.method = "GET"
    api.path = ["api", "job", "output", _]
    api.token.type = "job"
    api.token.job.state = job_state[_]
}

# Allow POST access to /api/job/* for valid job tokens
allow {
    api.method = "POST"
    api.path = ["api", "job", suffix]
    job_suffix := {"cache", "output", "create_jobs", "consoleupdate", "stats", "markup", "badge", "testresult"}
    suffix = job_suffix[_]
    api.token.type = "job"
    api.token.job.state = job_state[_]
}

# Allow POST access to /api/job/archive for valid job tokens (for service uploads)
allow {
    api.method = "POST"
    api.path = ["api", "job", "archive"]
    api.token.type = "job"
}
