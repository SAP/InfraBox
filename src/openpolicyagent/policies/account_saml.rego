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

allow {
    api.method = "GET"
    api.path = ["saml", "metadata"]
}

allow {
    api.method = "GET"
    api.path = ["saml", "initiate-logout"]
}

allow {
    api.method = "GET"
    api.path = ["saml", "logout"]
}