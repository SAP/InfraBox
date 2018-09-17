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

# Allow GET access to /api/job/job for valid job tokens
allow {
    http_api.method = "GET"
    http_api.path = ["api", "job", "job"]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}

# Allow GET access to /api/job/source for valid job tokens
allow {
    http_api.method = "GET"
    http_api.path = ["api", "job", "source"]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}

# Allow GET and POST access to /api/job/cache for valid job tokens
allow {
    http_api.method = ["GET", "POST"][_]
    http_api.path = ["api", "job", "cache"]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}

# Allow POST access to /api/job/archive for valid job tokens
allow {
    http_api.method = "POST"
    http_api.path = ["api", "job", "archive"]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}

# Allow POST access to /api/job/output for valid job tokens
allow {
    http_api.method = "POST"
    http_api.path = ["api", "job", "output"]
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

# Allow POST access to /api/job/create_jobs for valid job tokens
allow {
    http_api.method = "POST"
    http_api.path = ["api", "job", "create_jobs"]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}

# Allow POST access to /api/job/consoleupdate for valid job tokens
allow {
    http_api.method = "POST"
    http_api.path = ["api", "job", "consoleupdate"]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}

# Allow POST access to /api/job/stats for valid job tokens
allow {
    http_api.method = "POST"
    http_api.path = ["api", "job", "stats"]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}

# Allow POST access to /api/job/markup for valid job tokens
allow {
    http_api.method = "POST"
    http_api.path = ["api", "job", "markup"]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}

# Allow POST access to /api/job/badge for valid job tokens
allow {
    http_api.method = "POST"
    http_api.path = ["api", "job", "badge"]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}

# Allow POST access to /api/job/testresult for valid job tokens
allow {
    http_api.method = "POST"
    http_api.path = ["api", "job", "testresult"]
    http_api.token.type = "job"
    http_api.token.job.state = ["queued", "running", "scheduled"][_]
}