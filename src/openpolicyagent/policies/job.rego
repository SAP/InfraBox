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


# Allow GET /api/v1/projects/<project_id>/jobs for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/restart for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "restart"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/abort for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "abort"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/testresults for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "testresults"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/tabs for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "tabs"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive/download for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive", "download"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive/download/all for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive", "download", "all"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/console for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "console"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/output for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "output"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/testruns for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "testruns"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/tests/history for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "tests", "history"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/badges for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "badges"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/stats for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "stats"]
    api.token.type = "project"
    api.token.project.id = project_id
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/cache/clear for project tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "cache", "clear"]
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
