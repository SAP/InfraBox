CREATE TABLE "global_token" (
    id          uuid DEFAULT gen_random_uuid() NOT NULL,
    description VARCHAR(255) NOT NULL,
    scope_push  BOOLEAN DEFAULT FALSE NOT NULL,
    scope_pull  BOOLEAN DEFAULT TRUE NOT NULL,
    user_id     uuid NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_at  TIMESTAMP DEFAULT NOW() NOT NULL,
    expires_at  TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
);

-- Access log for audit trail.
-- Recommended retention: prune rows older than 90 days periodically, e.g.:
--   DELETE FROM global_token_access_log WHERE accessed_at < NOW() - INTERVAL '90 days';
CREATE TABLE global_token_access_log (
    id          uuid DEFAULT gen_random_uuid() NOT NULL,
    token_id    uuid NOT NULL REFERENCES global_token(id) ON DELETE CASCADE,
    accessed_at TIMESTAMP DEFAULT NOW() NOT NULL,
    path        TEXT NOT NULL,
    method      VARCHAR(10) NOT NULL,
    status_code SMALLINT,
    PRIMARY KEY (id)
);

CREATE INDEX idx_gtal_token_id    ON global_token_access_log(token_id);
CREATE INDEX idx_gtal_accessed_at ON global_token_access_log(accessed_at);
