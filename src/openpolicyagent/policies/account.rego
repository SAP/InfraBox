package infrabox

# HTTP API request
import input as http_api

allow {
    http_api.method = "POST"
    http_api.path = ["api", "v1", "account", "login"]
}

allow {
    http_api.method = "POST"
    http_api.path = ["api", "v1", "account", "register"]
}