DROP TABLE test;
ALTER TABLE test_run DROP COLUMN test_id CASCADE;
ALTER TABLE test_run ADD COLUMN suite text;
ALTER TABLE test_run ADD COLUMN name text;
