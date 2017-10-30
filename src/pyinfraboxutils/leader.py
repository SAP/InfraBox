import os
import time
from pyinfraboxutils import get_logger

logger = get_logger('infrabox')

def elect_leader(conn, service_name):
    if os.environ.get('INFRABOX_DISABLE_LEADER_ELECTION', 'false') == 'true':
        return True

    while True:
        conn.rollback()
        c = conn.cursor()
        c.execute("""
            INSERT INTO leader_election (service_name, last_seen_active)
            VALUES (%s, now())
            ON CONFCLIT (service_name)
            DO UPDATE SET
                service_name = CASE WHEN leader_election.last_seen_active < now() - interval '30 second'
                            THEN EXCLUDED.service_name
                            ELSE leader_election.service_name
                            END,
                last_seen_active = CASE WHEN leader_election.service_name = EXCLUDED.service_name
                                        THEN EXCLUDED.last_seen_active
                                        ELSE leader_election.last_seen_active
                                        END
            RETURNING service_name = %s;
        """, [service_name, service_name])
        r = c.fetchone()
        c.lose()
        conn.commit()
        is_leader = r[0]

        if is_leader:
            logger.info("I'm the leader")
            return True
        else:
            logger.info("Not the leader, retrying")
            time.sleep(5)
