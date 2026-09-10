-- Add index on job.created_at to speed up time-range queries.
--
-- Without this index, any query filtering by created_at (e.g. Grafana
-- dashboards, build activity reports) performs a full sequential scan on the
-- job table.
CREATE INDEX IF NOT EXISTS job_created_at_idx ON job USING btree (created_at);
