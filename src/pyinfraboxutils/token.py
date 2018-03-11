import jwt
import os

private_key_path = os.environ.get('INFRABOX_RSA_PRIVATE_KEY_PATH', '/var/run/secrets/infrabox.net/rsa/id_rsa')
public_key_path = os.environ.get('INFRABOX_RSA_PUBLIC_KEY_PATH', '/var/run/secrets/infrabox.net/rsa/id_rsa.pub')

private_key = None
with open(private_key_path) as s:
    private_key = s.read()

public_key = None
with open(public_key_path) as s:
    public_key = s.read()

def encode_user_token(user_id):
    data = {
        'user': {
            'id': user_id
        },
        'type': 'user'
    }

    return jwt.encode(data, key=private_key, algorithm='RS256')

def encode_project_token(token_id, project_id):
    data = {
        'id': token_id,
        'project': {
            'id': project_id
        },
        'type': 'project'
    }

    return jwt.encode(data, key=private_key, algorithm='RS256')

def encode_job_token(job_id):
    data = {
        'job': {
            'id': job_id
        },
        'type': 'job'
    }

    return jwt.encode(data, key=private_key, algorithm='RS256')

def decode(encoded):
    return jwt.decode(encoded, key=public_key, algorithm='RS256')
