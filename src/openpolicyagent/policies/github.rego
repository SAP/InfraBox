package infrabox

# HTTP API request
import input as http_api

# GitHub Auth Namespace

allow {
    http_api.method = "GET"
    http_api.path = ["github", "auth", "connect"]
    http_api.token.type = "user"
}

# GitHub Namespace

allow {
    http_api.method = "GET"
    http_api.path = ["api", "v1", "github", "repos"]
    http_api.token.type = "user"
}