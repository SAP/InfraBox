-- Temporary read-tokens for decrypted secret values.
--
-- A project administrator applies for one of these tokens; it is valid for a
-- short, fixed window (20 minutes) and is required, in addition to the normal
-- admin session token, to read decrypted secret values via
-- GET /api/v1/projects/<project_id>/secrets/values.
--
-- Token format: ib_secret_read_<48 hex chars>
-- Lookup key:   first 16 chars of the 48-char hex suffix (token_id)
-- Hash:         SHA-256 of the full raw token string (UTF-8) — raw token is
--               never stored.
CREATE TABLE secret_read_token (
    token_id      VARCHAR(16)  NOT NULL,
    token_hash    VARCHAR(64)  NOT NULL,
    project_id    uuid         NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    user_id       uuid         NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    expires_at    TIMESTAMP    NOT NULL,
    revoked_at    TIMESTAMP,
    last_used_at  TIMESTAMP,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    PRIMARY KEY (token_id)
);

CREATE INDEX idx_secret_read_token_hash    ON secret_read_token(token_hash);
CREATE INDEX idx_secret_read_token_project ON secret_read_token(project_id, user_id);
