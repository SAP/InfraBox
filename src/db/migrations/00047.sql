-- Migration 00047: ensure expires_at exists on global_token.
-- Uses a DO block for compatibility with PostgreSQL 9.5 (IF NOT EXISTS on
-- ADD COLUMN was only added in 9.6).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'global_token' AND column_name = 'expires_at'
    ) THEN
        ALTER TABLE global_token ADD COLUMN expires_at TIMESTAMP NOT NULL DEFAULT NOW() + INTERVAL '365 days';
    END IF;
END $$;
