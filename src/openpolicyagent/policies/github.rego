package infrabox

# HTTP API request
import input as api

# GitHub Auth Namespace

allow {
    api.method = "GET"
    api.path = ["github", "auth", "connect"]
    api.token.type = "user"
}

# GitHub Namespace

allow {
    api.method = "GET"
    api.path = ["api", "v1", "github", "repos"]
    api.token.type = "user"
}

allow {
    api.method = "GET"
    api.path = ["github", "auth"]
}

allow {
    api.method = "GET"
    api.path = ["github", "auth", "callback"]
}