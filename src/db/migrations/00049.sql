-- Add index on build.created_at to speed up time-range queries.
--
-- Without this index, any query filtering by created_at (e.g. Grafana
-- dashboards, build activity reports) performs a full sequential scan on the
-- build table.
CREATE INDEX IF NOT EXISTS build_created_at_idx ON build USING btree (created_at);
