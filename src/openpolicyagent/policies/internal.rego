package infrabox

# HTTP API request
import input as api

allow {
    api.method = "POST"
    api.path = ["internal", "api", "job", "consoleupdate"]
}

allow {
    api.method = "POST"
    api.path = ["internal", "api", "projects", _, "trigger"]
}
