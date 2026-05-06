-- Global tokens are now owned by individual users (personal viewer tokens).
-- Each user manages their own tokens; scope is limited to their accessible projects.
ALTER TABLE global_token
    ADD COLUMN user_id uuid REFERENCES "user"(id) ON DELETE CASCADE,
    ADD COLUMN created_at TIMESTAMP DEFAULT NOW() NOT NULL;

-- Remove legacy admin-created tokens that have no owner
DELETE FROM global_token WHERE user_id IS NULL;

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
