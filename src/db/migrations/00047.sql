CREATE TABLE mcp_token (
    token_id      VARCHAR(16)  NOT NULL,
    token_hash    VARCHAR(64)  NOT NULL,
    user_id       uuid         NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    name          VARCHAR(128) NOT NULL,
    enabled_projects JSONB     NOT NULL DEFAULT '{}',
    allow_trigger BOOLEAN      NOT NULL DEFAULT FALSE,
    expires_at    TIMESTAMP    NOT NULL,
    revoked_at    TIMESTAMP,
    last_used_at  TIMESTAMP,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    PRIMARY KEY (token_id)
);

CREATE INDEX idx_mcp_token_user_id ON mcp_token(user_id);
CREATE INDEX idx_mcp_token_hash    ON mcp_token(token_hash);

-- Audit log for all MCP API calls.
-- Retention: rows older than 90 days should be pruned periodically, e.g.:
--   DELETE FROM mcp_access_log WHERE accessed_at < NOW() - INTERVAL '90 days';
CREATE TABLE mcp_access_log (
    id          uuid         DEFAULT gen_random_uuid() NOT NULL,
    token_id    VARCHAR(16),
    user_id     uuid,
    action      VARCHAR(128) NOT NULL,
    outcome     VARCHAR(32)  NOT NULL,
    details     JSONB,
    error       TEXT,
    ip          VARCHAR(64),
    accessed_at TIMESTAMP    NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id)
);

CREATE INDEX idx_mcp_access_log_token_id    ON mcp_access_log(token_id);
CREATE INDEX idx_mcp_access_log_accessed_at ON mcp_access_log(accessed_at);
