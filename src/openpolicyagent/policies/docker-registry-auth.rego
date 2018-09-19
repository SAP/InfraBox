package infrabox

import input as api

# Allow GET access to /ping for all
allow {
    api.method = "GET"
    api.path = ["ping"]
}

