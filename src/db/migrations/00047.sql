ALTER TABLE global_token ADD COLUMN expires_at TIMESTAMP;
UPDATE global_token SET expires_at = created_at + INTERVAL '1 year';
ALTER TABLE global_token ALTER COLUMN expires_at SET NOT NULL;
