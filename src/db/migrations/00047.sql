-- Migration 00047: ensure expires_at exists on global_token.
-- Required because migration 00045 was initially shipped without this column
-- on some clusters, and the CREATE TABLE in 00045 was a no-op on those
-- that had an older global_token table from a prior deployment.
ALTER TABLE global_token ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP NOT NULL DEFAULT NOW() + INTERVAL '365 days';
