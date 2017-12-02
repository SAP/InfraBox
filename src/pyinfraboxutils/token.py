import jwt

def encode_user_token(user_id):
    with open('/var/run/secrets/infrabox.net/rsa/id_rsa') as secret:
        data = {
            'user': {
                'id': user_id
            },
            'type': 'user'
        }

        token = jwt.encode(data, key=secret.read(), algorithm='RS256')
        return str(token)

def encode_project_token(token):
    with open('/var/run/secrets/infrabox.net/rsa/id_rsa') as secret:
        data = {
            'project': {
                'token': token
            },
            'type': 'project'
        }

        token = jwt.encode(data, key=secret.read(), algorithm='RS256')
        return str(token)

def encode_job_token(job_id):
    with open('/var/run/secrets/infrabox.net/rsa/id_rsa') as secret:
        data = {
            'job': {
                'id': job_id
            },
            'type': 'job'
        }

        token = jwt.encode(data, key=secret.read(), algorithm='RS256')
        return str(token)


def decode(encoded):
    with open('/var/run/secrets/infrabox.net/rsa/id_rsa.pub') as secret:
        return jwt.decode(encoded, key=secret.read(), algorithm='RS256')
