package infrabox

# HTTP API request
import input as http_api

# Allow administrators access to everything
allow {
    http_api.token.type = "user"
    http_api.token.user_id = "00000000-0000-0000-0000-000000000000"
}

# Allow GET access to /api/v1/admin/clusters for users logged in
allow {
    http_api.method = "GET"
    http_api.path = ["api", "v1", "admin", "clusters"]
    http_api.token.type = "user"
}