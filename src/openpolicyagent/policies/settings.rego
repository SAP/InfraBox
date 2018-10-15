package infrabox

# HTTP API request
import input as api

# Allow GET access to /api/v1/settings for anyone
allow {
    api.method = "GET"
    api.path = ["api", "v1", "settings"]
}