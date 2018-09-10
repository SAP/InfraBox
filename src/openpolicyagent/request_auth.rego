package httpapi.authz


# HTTP API request
import input as http_api

default allow = false

allow {
    http_api.method = "GET"
    http_api.path = ["api", "v1", "settings"]
}
