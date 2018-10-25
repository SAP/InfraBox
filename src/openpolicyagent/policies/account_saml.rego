package infrabox

# HTTP API request
import input as api

allow {
    api.method = "GET"
    api.path = ["saml", "auth"]
}

allow {
    api.method = "POST"
    api.path = ["saml", "callback"]
}