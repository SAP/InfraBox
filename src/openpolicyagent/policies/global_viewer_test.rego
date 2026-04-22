package infrabox

# ─── helpers ───────────────────────────────────────────────────────────────────

global_viewer_token = {
    "type": "global",
    "user": {"id": null, "role": "viewer"},
    "global_token": {"id": "00000000-0000-0000-0000-000000000001",
                     "scope_push": false, "scope_pull": true}
}

user_viewer_token = {
    "type": "user",
    "user": {"id": "00000000-0000-0000-0000-000000000002", "role": "viewer"}
}

# ─── global token: read-only allowed ───────────────────────────────────────────

test_global_viewer_can_get_admin_users {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "admin", "users"],
        "token": global_viewer_token
    }
}

test_global_viewer_can_get_admin_clusters {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "admin", "clusters"],
        "token": global_viewer_token
    }
}

test_global_viewer_can_get_projects_list {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects"],
        "token": global_viewer_token
    }
}

test_global_viewer_can_get_project_by_id {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099"],
        "token": global_viewer_token
    }
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

# ─── user viewer role: read-only allowed ───────────────────────────────────────

test_user_viewer_can_get_admin_users {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "admin", "users"],
        "token": user_viewer_token
    }
}

test_user_viewer_can_get_projects_list {
    authz with input as {
        "method": "GET",
        "path": ["api", "v1", "projects"],
        "token": user_viewer_token
    }
}

# ─── user viewer role: write MUST be denied ────────────────────────────────────

test_user_viewer_cannot_post_admin_users {
    not authz with input as {
        "method": "POST",
        "path": ["api", "v1", "admin", "users"],
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

test_regular_user_can_post_projects {
    authz with input as {
        "method": "POST",
        "path": ["api", "v1", "projects"],
        "token": {
            "type": "user",
            "user": {"id": "00000000-0000-0000-0000-000000000004", "role": "user"}
        }
    }
}

test_user_viewer_cannot_delete_project {
    not authz with input as {
        "method": "DELETE",
        "path": ["api", "v1", "projects", "00000000-0000-0000-0000-000000000099"],
        "token": user_viewer_token
    }
}

# ─── global-tokens endpoint: only admin can manage ─────────────────────────────

test_global_viewer_cannot_post_global_tokens {
    not authz with input as {
        "method": "POST",
        "path": ["api", "v1", "admin", "global-tokens"],
        "token": global_viewer_token
    }
}

test_admin_can_post_global_tokens {
    authz with input as {
        "method": "POST",
        "path": ["api", "v1", "admin", "global-tokens"],
        "token": {
            "type": "user",
            "user": {"id": "00000000-0000-0000-0000-000000000003", "role": "admin"}
        }
    }
}
