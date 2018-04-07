# Dummy Data
For development you can quickly start a postgres and minio with some dummy data.
In this directory run:

```
    $ docker-compose up
```

The services will be available:

Service|Address
-------|-------
Postgres|localhost:5439
Minio|localhost:9009

## Data
The following projects and users are created

### Project 1

Project:
- Name: upload1
- Type: upload

User:
- username: user1
- is collaborator of project 'upload1'

Auth Token:
- ID: 00000000-0000-0000-0000-000000000002

Secret:
- Name: SECRET_ENV
