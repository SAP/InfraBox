package infrabox

# HTTP API request
import input as api

user_roles = {"user": 10, "devops": 20, "admin": 30}

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


