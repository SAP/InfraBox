package infrabox

# HTTP API request
import input as api

roles = {"Developer": 10, "Administrator": 20, "Owner": 30}

allow {
    api.method = "GET"
    api.path = ["api", "v1", "user"]
    api.token.type = "user"
}
