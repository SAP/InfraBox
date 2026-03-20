package infrabox

# HTTP API request
import input as api

user_roles = {"viewer": 15, "user": 10, "devops": 20, "admin": 30}

default authz = false

# deny will overwrite allow
authz {
    allow
    not deny
}


# Allow admin and devops access to everything
allow {
    api.token.type = "user"
    user_roles[api.token.user.role] >= 20
}

# Allow viewer role GET access to all admin endpoints
allow {
    api.method = "GET"
    api.token.type = "user"
    api.token.user.role = "viewer"
}

# Allow global token (viewer) GET access to all admin endpoints
allow {
    api.method = "GET"
    api.token.type = "global"
    api.token.user.role = "viewer"
}

# Allow admin access to manage global tokens
allow {
    api.path[0] = "api"
    api.path[1] = "v1"
    api.path[2] = "admin"
    api.path[3] = "global-tokens"
    api.token.type = "user"
    user_roles[api.token.user.role] >= 30
}


# Allow GET access to /api/v1/admin/clusters for users logged in
allow {
    api.method = "GET"
    api.path = ["api", "v1", "admin", "clusters"]
    api.token.type = "user"
}

# Allow POST access to /api/v1/admin/clusters for admin
allow {
    api.method = "POST"
    api.path = ["api", "v1", "admin", "clusters"]
    api.token.type = "user"
    user_roles[api.token.user.role] >= 20
}


# Deny POST access to /api/v1/admin/clusters for devops and user, only allowed for admin
deny {
    api.method = "POST"
    api.path = ["api", "v1", "admin", "users"]
    api.token.type = "user"
    user_roles[api.token.user.role] <= 20
}


