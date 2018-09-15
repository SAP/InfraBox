ALTER TABLE job DROP COLUMN memory, DROP COLUMN cpu, DROP COLUMN build_only, DROP COLUMN timeout, DROP COLUMN security_context, DROP COLUMN resources;
UPDATE job SET definition = '{}' WHERE definition IS NULL;
ALTER TABLE job ALTER COLUMN definition SET NOT NULL;
