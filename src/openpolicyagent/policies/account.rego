package infrabox

# HTTP API request
import input as api

allow {
    api.method = "POST"
    api.path = ["api", "v1", "account", "login"]
}

allow {
    api.method = "POST"
    api.path = ["api", "v1", "account", "register"]
}