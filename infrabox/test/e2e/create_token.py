import sys
import jwt

if len(sys.argv) < 4:
    print("Usage: create_token.py <path_to_private_key> <project_id> <token_id>")
    sys.exit(1)

with open(sys.argv[1]) as key:
    data = {
        'id': sys.argv[3],
        'project': {
            'id': sys.argv[2]
        },
        'type': 'project'
    }

    encoded = jwt.encode(data, key.read(), algorithm='RS256')
    print(encoded)
