import sys
import os
import htpasswd

if "INFRABOX_DOCKER_REGISTRY_ADMIN_USERNAME" not in os.environ:
    print("INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD not set")
    sys.exit(1)

if "INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD" not in os.environ:
    print("INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD not set")
    sys.exit(1)

if "HTPASSWD_PATH" not in os.environ:
    print("HTPASSWD_PATH not set")
    sys.exit(1)

admin_user = os.environ['INFRABOX_DOCKER_REGISTRY_ADMIN_USERNAME']
admin_password = os.environ['INFRABOX_DOCKER_REGISTRY_ADMIN_PASSWORD']

open(os.environ['HTPASSWD_PATH'], 'w')
with htpasswd.Basic(os.environ['HTPASSWD_PATH'], mode="md5") as userdb:
    try:
        userdb.add(admin_user, admin_password)
    except htpasswd.basic.UserExists, e:
        print(e)
