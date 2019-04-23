import os
import time
import sys
from pyinfraboxutils import get_logger

logger = get_logger('infrabox')

def _is_leader(conn, service_name, cluster_name=None):
    if os.environ.get('INFRABOX_DISABLE_LEADER_ELECTION', 'false') == 'true':
        return True

    conn.rollback()
    c = conn.cursor()
    c.execute("""
        INSERT INTO leader_election (service_name, cluster_name, last_seen_active)
        VALUES (%s, %s, now())
        ON CONFLICT (service_name)
        DO UPDATE SET
            cluster_name = CASE WHEN leader_election.last_seen_active < now() - interval '30 second'
                        THEN EXCLUDED.cluster_name
                        ELSE leader_election.cluster_name
                        END,
            last_seen_active = CASE WHEN leader_election.cluster_name = EXCLUDED.cluster_name
                                    THEN EXCLUDED.last_seen_active
                                    ELSE leader_election.last_seen_active
                                    END
        RETURNING service_name, cluster_name;
    """, [service_name, cluster_name])
    r = c.fetchone()
    c.close()
    conn.commit()
    return r == (service_name, cluster_name)

def is_leader(conn, service_name, cluster_name=None, exit=True):
    leader = _is_leader(conn, service_name, cluster_name)

    if not leader:
        logger.warning('Not the leader anymore')
        if exit:
            sys.exit(1)
        else:
            return False

    return True

def elect_leader(conn, service_name, cluster_name=None):
    while True:
        leader = _is_leader(conn, service_name, cluster_name)
        if leader:
            logger.info("I'm the leader")
            return True
        else:
            logger.warning("Not the leader, retrying")
            time.sleep(5)

def is_active(conn, cluster_name):
    c = conn.cursor()
    c.execute("""
        SELECT active, enabled
        FROM cluster
        WHERE name = %s """, [cluster_name])
    active, enabled = c.fetchone()
    c.close()

    return active and enabled
