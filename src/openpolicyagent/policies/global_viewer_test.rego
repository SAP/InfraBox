package infrabox

# ─── helpers ───────────────────────────────────────────────────────────────────

# Global token owned by user 002; user 002 is a collaborator on project 099
global_viewer_token = {
    "type": "global",
    "user": {"id": "00000000-0000-0000-0000-000000000002", "role": "viewer"},
    "global_token": {"id": "00000000-0000-0000-0000-000000000001",
                     "scope_push": false, "scope_pull": true}
}

user_viewer_token = {
    "type": "user",
    "user": {"id": "00000000-0000-0000-0000-000000000002", "role": "viewer"}
}

user_normal_token = {
    "type": "user",
    "user": {"id": "00000000-0000-0000-0000-000000000004", "role": "user"}
}

admin_token = {
    "type": "user",
    "user": {"id": "00000000-0000-0000-0000-000000000003", "role": "admin"}
}

# ─── global token: project list (filtered by collaborator on Python side) ──────

test_global_viewer_can_get_projects_list {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects"],
        "token": global_viewer_token
    }
}

# Collaborator check: user 002 IS a collaborator on project 099
test_global_viewer_can_get_collaborator_project {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099"],
        "token": global_viewer_token
    } with data.infrabox.collaborators.collaborators as [
        {"user_id": "00000000-0000-0000-0000-000000000002",
         "project_id": "00000000-0000-0000-0000-000000000099",
         "role": "Developer"}
    ]
}

# Collaborator check: user 002 is NOT a collaborator on project 098 → denied
test_global_viewer_cannot_get_non_collaborator_project {
    not authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000098"],
        "token": global_viewer_token
    } with data.infrabox.collaborators.collaborators as [
        {"user_id": "00000000-0000-0000-0000-000000000002",
         "project_id": "00000000-0000-0000-0000-000000000099",
         "role": "Developer"}
    ]
}

# ─── global token: write MUST be denied ────────────────────────────────────────

test_global_viewer_cannot_post_projects {
    not authz with input as {
        "method": "POST",
        "path": ["api", "v1", "projects"],
        "token": global_viewer_token
    }
}

test_global_viewer_cannot_delete_project {
    not authz with input as {
        "method": "DELETE",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099"],
        "token": global_viewer_token
    }
}

# ─── global token: admin endpoints MUST be denied ─────────────────────────────

test_global_viewer_cannot_get_admin_users {
    not authz with input as {
        "method": "GET",
        "path": ["api", "v1", "admin", "users"],
        "token": global_viewer_token
    }
}

test_global_viewer_cannot_post_admin_users {
    not authz with input as {
        "method": "POST",
        "path": ["api", "v1", "admin", "users"],
        "token": global_viewer_token
    }
}

test_global_viewer_cannot_delete_admin_clusters {
    not authz with input as {
        "method": "DELETE",
        "path": ["api", "v1", "admin", "clusters"],
        "token": global_viewer_token
    }
}

test_global_viewer_cannot_post_global_tokens {
    not authz with input as {
        "method": "POST",
        "path": ["api", "v1", "admin", "global-tokens"],
        "token": global_viewer_token
    }
}

# ─── user token management: any user can manage own tokens ────────────────────

test_normal_user_can_list_own_tokens {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "user", "global-tokens"],
        "token": user_normal_token
    }
}

test_normal_user_can_create_token {
    authz with input as {
        "method": "POST",
        "path": ["api", "v1", "user", "global-tokens"],
        "token": user_normal_token
    }
}

test_normal_user_can_delete_own_token {
    authz with input as {
        "method": "DELETE",
        "path": ["api", "v1", "user", "global-tokens", "00000000-0000-0000-0000-000000000001"],
        "token": user_normal_token
    }
}

test_normal_user_can_read_access_log {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "user", "global-tokens", "00000000-0000-0000-0000-000000000001", "access-log"],
        "token": user_normal_token
    }
}

# Viewer-role user cannot create tokens
test_viewer_user_cannot_create_token {
    not authz with input as {
        "method": "POST",
        "path": ["api", "v1", "user", "global-tokens"],
        "token": user_viewer_token
    }
}

# ─── admin audit: only admin can read all tokens ──────────────────────────────

test_admin_can_list_all_global_tokens {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "admin", "global-tokens"],
        "token": admin_token
    }
}

test_normal_user_cannot_list_all_global_tokens {
    not authz with input as {
        "method": "GET",
        "path": ["api", "v1", "admin", "global-tokens"],
        "token": user_normal_token
    }
}

# ─── user viewer role: read access ────────────────────────────────────────────

test_user_viewer_can_get_projects_list {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects"],
        "token": user_viewer_token
    }
}

test_user_viewer_cannot_post_projects {
    not authz with input as {
        "method": "POST",
        "path": ["api", "v1", "projects"],
        "token": user_viewer_token
    }
}

test_user_viewer_cannot_delete_project {
    not authz with input as {
        "method": "DELETE",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099"],
        "token": user_viewer_token
    }
}

test_regular_user_can_post_projects {
    authz with input as {
        "method": "POST",
        "path": ["api", "v1", "projects"],
        "token": user_normal_token
    }
}

# ─── global token: builds and jobs read access ────────────────────────────────

test_global_viewer_can_list_builds {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099", "builds"],
        "token": global_viewer_token
    } with data.infrabox.collaborators.collaborators as [
        {"user_id": "00000000-0000-0000-0000-000000000002",
         "project_id": "00000000-0000-0000-0000-000000000099",
         "role": "Developer"}
    ]
}

test_global_viewer_can_get_build {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099", "builds", "00000000-0000-0000-0000-000000000010"],
        "token": global_viewer_token
    } with data.infrabox.collaborators.collaborators as [
        {"user_id": "00000000-0000-0000-0000-000000000002",
         "project_id": "00000000-0000-0000-0000-000000000099",
         "role": "Developer"}
    ]
}

test_global_viewer_can_get_job_console {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099", "jobs", "00000000-0000-0000-0000-000000000020", "console"],
        "token": global_viewer_token
    } with data.infrabox.collaborators.collaborators as [
        {"user_id": "00000000-0000-0000-0000-000000000002",
         "project_id": "00000000-0000-0000-0000-000000000099",
         "role": "Developer"}
    ]
}

test_global_viewer_can_get_job_stats {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099", "jobs", "00000000-0000-0000-0000-000000000020", "stats"],
        "token": global_viewer_token
    } with data.infrabox.collaborators.collaborators as [
        {"user_id": "00000000-0000-0000-0000-000000000002",
         "project_id": "00000000-0000-0000-0000-000000000099",
         "role": "Developer"}
    ]
}

test_global_viewer_cannot_list_builds_non_collaborator {
    not authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000098", "builds"],
        "token": global_viewer_token
    } with data.infrabox.collaborators.collaborators as [
        {"user_id": "00000000-0000-0000-0000-000000000002",
         "project_id": "00000000-0000-0000-0000-000000000099",
         "role": "Developer"}
    ]
}

# ─── global token: write operations require scope_push ────────────────────────

global_viewer_push_token = {
    "type": "global",
    "user": {"id": "00000000-0000-0000-0000-000000000002", "role": "viewer"},
    "global_token": {"id": "00000000-0000-0000-0000-000000000001",
                     "scope_push": true, "scope_pull": true}
}

test_global_viewer_cannot_restart_build_without_scope_push {
    not authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099", "builds", "00000000-0000-0000-0000-000000000010", "restart"],
        "token": global_viewer_token
    } with data.infrabox.collaborators.collaborators as [
        {"user_id": "00000000-0000-0000-0000-000000000002",
         "project_id": "00000000-0000-0000-0000-000000000099",
         "role": "Developer"}
    ]
}

test_global_push_can_restart_build {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099", "builds", "00000000-0000-0000-0000-000000000010", "restart"],
        "token": global_viewer_push_token
    } with data.infrabox.collaborators.collaborators as [
        {"user_id": "00000000-0000-0000-0000-000000000002",
         "project_id": "00000000-0000-0000-0000-000000000099",
         "role": "Developer"}
    ]
}

test_global_viewer_cannot_trigger_without_scope_push {
    not authz with input as {
        "method": "POST",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099", "trigger"],
        "token": global_viewer_token
    } with data.infrabox.collaborators.collaborators as [
        {"user_id": "00000000-0000-0000-0000-000000000002",
         "project_id": "00000000-0000-0000-0000-000000000099",
         "role": "Developer"}
    ]
}

test_global_push_can_trigger {
    authz with input as {
        "method": "POST",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099", "trigger"],
        "token": global_viewer_push_token
    } with data.infrabox.collaborators.collaborators as [
        {"user_id": "00000000-0000-0000-0000-000000000002",
         "project_id": "00000000-0000-0000-0000-000000000099",
         "role": "Developer"}
    ]
}
