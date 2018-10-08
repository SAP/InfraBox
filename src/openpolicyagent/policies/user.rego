package infrabox

# HTTP API request
import input as api

roles = {"Developer": 1, "Administrator": 2, "Owner": 3}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "user"]
    api.token.type = "user"
}
