package infrabox

# HTTP API request
import input as api

allow {
    api.method = "GET"
    api.path = ["internal", "api", "job", "consoleupdate"]
}
