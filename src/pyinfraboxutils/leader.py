import os
import time
import requests
from pyinfraboxutils import get_logger

logger = get_logger('infrabox')

def elect_leader():
    if os.environ.get('INFRABOX_DISABLE_LEADER_ELECTION', 'false') == 'true':
        return

    while True:
        r = requests.get("http://localhost:4040", timeout=5)
        leader = r.json()['name']

        if leader == os.environ['HOSTNAME']:
            logger.info("I'm the leader")
            break
        else:
            logger.info("I'm not the leader, %s is the leader", leader)
            time.sleep(1)
