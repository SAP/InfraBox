package infrabox

import input as api

import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects

project_jobs_collaborator([user, project_id]) {
    collaborators[i].project_id = project_id
    collaborators[i].user_id = user
}

project_jobs_public(project){
    projects[i].id = project
    projects[i].public = true
}

valid_project_token([token, project_id]) {
    token.type = "project"
    token.project.id = project_id
}

# Allow GET /api/v1/projects/<id>/jobs for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<id>/jobs if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<id>/jobs for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/restart for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "restart"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/restart for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "restart"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/rerun for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "rerun"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/rerun for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "rerun"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/abort for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "abort"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/abort for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "abort"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/testresults for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "testresults"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/testresults for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "testresults"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/testresults if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "testresults"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/testresults for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "testresults"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/tabs for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "tabs"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/tabs if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "tabs"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/tabs if project for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "tabs"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive/download for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive", "download"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive/download if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive", "download"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive/download for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive", "download"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive/download/all for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive", "download", "all"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive/download/all if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive", "download", "all"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/archive/download/all for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "archive", "download", "all"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/console for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "console"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/console if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "console"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/console for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "console"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/output for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "output"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/output if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "output"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/output for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "output"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/testruns for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "testruns"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/testruns if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "testruns"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/testruns for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "testruns"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/tests/history for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "tests", "history"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/tests/history if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "tests", "history"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/tests/history for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "tests", "history"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/badges for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "badges"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/badges if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "badges"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/badges for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "badges"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/stats for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "stats"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/stats if project is public
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "stats"]
    project_jobs_public(project_id)
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/stats for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "stats"]
    valid_project_token([api.token, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/cache/clear for collaborators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "cache", "clear"]
    api.token.type = "user"
    project_jobs_collaborator([api.token.user.id, project_id])
}

# Allow GET /api/v1/projects/<project_id>/jobs/<job_id>/cache/clear for valid project token
allow {
    api.method = "GET"
    api.path = ["api", "v1", "projects", project_id, "jobs", _, "cache", "clear"]
    valid_project_token([api.token, project_id])
}
