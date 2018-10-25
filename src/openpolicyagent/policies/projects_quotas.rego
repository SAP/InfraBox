package infrabox

import input as api

import data.infrabox.collaborators.collaborators
import data.infrabox.admin.admin
import data.infrabox.roles


admin_quotas_administrator(user){
    user = "00000000-0000-0000-0000-000000000000"
}



# Allow GET access to /api/v1/admin/quotas for project administrators
allow {
    api.method = "GET"
    api.path = ["api", "v1", "admin", "quotas"]
    api.token.type = "user"
    admin_quotas_administrator(api.token.user.id)
}

# Allow POST access to /api/v1/admin/quotas for project administrators
allow {
    api.method = "POST"
    api.path = ["api", "v1", "admin", "quotas"]
    api.token.type = "user"
    admin_quotas_administrator(api.token.user.id)
}

# Allow DELETE access to /api/v1/admin/quotas for project administrators
allow {
    api.method = "DELETE"
    api.path = ["api", "v1", "admin", "quotas"]
    api.token.type = "user"
    admin_quotas_administrator(api.token.user.id)
}