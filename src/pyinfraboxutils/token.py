import jwt

def encode_user_token(user_id):
    with open('/var/run/secrets/infrabox.net/rsa/id_rsa') as secret:
        data = {
            'user': {
                'id': user_id
            },
            'type': 'user'
        }

        return jwt.encode(data, key=secret.read(), algorithm='RS256')

def encode_project_token(token, project_id):
    with open('/var/run/secrets/infrabox.net/rsa/id_rsa') as secret:
        data = {
            'id': token,
            'project': {
                'id': project_id
            },
            'type': 'project'
        }

        return jwt.encode(data, key=secret.read(), algorithm='RS256')

def encode_job_token(job_id):
    with open('/var/run/secrets/infrabox.net/rsa/id_rsa') as secret:
        data = {
            'job': {
                'id': job_id
            },
            'type': 'job'
        }

        return jwt.encode(data, key=secret.read(), algorithm='RS256')

def decode(encoded):
    with open('/var/run/secrets/infrabox.net/rsa/id_rsa.pub') as secret:
        return jwt.decode(encoded, key=secret.read(), algorithm='RS256')
