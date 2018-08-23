DROP TRIGGER job_queue_notify_update ON job;
CREATE TRIGGER job_queue_notify_update AFTER UPDATE ON job FOR EACH ROW WHEN (OLD.state IS DISTINCT FROM NEW.state) EXECUTE PROCEDURE job_queue_notify();
