package infrabox

# HTTP API request
import input as http_api

# Allow GET access to /api/v1/settings for anyone
allow {
    http_api.method = "GET"
    http_api.path = ["api", "v1", "settings"]
}