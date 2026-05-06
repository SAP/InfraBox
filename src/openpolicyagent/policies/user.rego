package infrabox

# HTTP API request
import input as api

roles = {"Developer": 10, "Administrator": 20, "Owner": 30}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "user"]
    api.token.type = "user"
}

# Any logged-in user can list their own global tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "user", "global-tokens"]
    api.token.type = "user"
}

# Any logged-in user (except viewer role) can create a global token
allow {
    api.method = "POST"
    api.path = ["api", "v1", "user", "global-tokens"]
    api.token.type = "user"
    api.token.user.role != "viewer"
}

# Any logged-in user can revoke their own global tokens
allow {
    api.method = "DELETE"
    api.path = ["api", "v1", "user", "global-tokens", _]
    api.token.type = "user"
}

# Any logged-in user can read the access log for their own tokens
allow {
    api.method = "GET"
    api.path = ["api", "v1", "user", "global-tokens", _, "access-log"]
    api.token.type = "user"
}
