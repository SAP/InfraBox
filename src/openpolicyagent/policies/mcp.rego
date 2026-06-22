package infrabox

# HTTP API request
import input as api

# Allow MCP bearer tokens on /api/v1/mcp/* data paths.
# mcp_auth_required validates the token and project scope per-request.
allow {
    api.token.type = "mcp"
    api.path[0] = "api"
    api.path[1] = "v1"
    api.path[2] = "mcp"
    not api.path[3] = "tokens"
}

# Deny MCP tokens on token management paths — session auth only.
deny {
    api.token.type = "mcp"
    api.path[0] = "api"
    api.path[1] = "v1"
    api.path[2] = "mcp"
    api.path[3] = "tokens"
}

# Allow session-authenticated users to manage their MCP tokens.
allow {
    api.token.type = "user"
    api.path[0] = "api"
    api.path[1] = "v1"
    api.path[2] = "mcp"
    api.path[3] = "tokens"
}
