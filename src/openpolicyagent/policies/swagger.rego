package infrabox

# HTTP API request
import input as api

# Allow GET access to /api/swagger.json for anyone
allow {
    api.method = "GET"
    api.path = ["api", "swagger.json"]
}
