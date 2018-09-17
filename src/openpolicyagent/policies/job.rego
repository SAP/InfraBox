package infrabox

# HTTP API request
import input as http_api

# job.py

# Allow GET access to api/v1/projects/<project_id>/jobs/<job_id> for project tokens
allow {
    http_api.method = "GET"
    http_api.path = ["api", "v1", "projects", project_id, "jobs", _]
    http_api.token.type = "project"
    http_api.token.project_id = project_id
}

# Allow GET access to api/v1/projects/<project_id>/jobs/<job_id>/output for project tokens
allow {
    http_api.method = "GET"
    http_api.path = ["api", "v1", "projects", project_id, "jobs", _, "output"]
    http_api.token.type = "project"
    http_api.token.project_id = project_id
}

# Allow GET access to api/v1/projects/<project_id>/jobs/<job_id>/manifest for project tokens
allow {
    http_api.method = "GET"
    http_api.path = ["api", "v1", "projects", project_id, "jobs", _, "manifest"]
    http_api.token.type = "project"
    http_api.token.project_id = project_id
}


# job_api.py

# Allow GET access to /api/job/* for valid job tokens
allow {
    http_api.method = "GET"
    http_api.path = ["api", "job", suffix]
    suffix = ["job", "source, cache"][_]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}

# Allow GET access to /api/job/output/<parent_job> for valid job tokens
allow {
    http_api.method = "GET"
    http_api.path = ["api", "job", "output", _]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}

# Allow POST access to /api/job/* for valid job tokens
allow {
    http_api.method = "POST"
    http_api.path = ["api", "job", suffix]
    suffix = ["cache", "archive", "output", "create_jobs", "consoleupdate", "stats", "markup", "badge", "testresult"][_]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}