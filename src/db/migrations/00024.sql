DROP TRIGGER job_queue_notify_update ON job;
CREATE TRIGGER job_queue_notify_update AFTER UPDATE ON job FOR EACH ROW WHEN (
    OLD.state IS DISTINCT FROM NEW.state OR
    OLD.restarted IS DISTINCT FROM NEW.restarted OR
    OLD.dependencies IS DISTINCT FROM NEW.dependencies
) EXECUTE PROCEDURE job_queue_notify();
