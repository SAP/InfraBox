package infrabox

# HTTP API request
import input as api

# Allow administrators access to everything
allow {
    api.token.type = "user"
    api.token.user.id = "00000000-0000-0000-0000-000000000000"
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
    api.token.user.id = "00000000-0000-0000-0000-000000000000"
}
