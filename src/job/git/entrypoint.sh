mkdir -p ~/.ssh

if [ -f /tmp/gerrit/id_rsa ]; then
    cp /tmp/gerrit/id_rsa ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -p $INFRABOX_GERRIT_PORT $INFRABOX_GERRIT_HOSTNAME >> ~/.ssh/known_hosts
fi

python /git/clone.py
