-------------------------------------------------------------------------
-- PROJECT 1
-- UserID (user1):                  '00000000-0000-0000-0000-000000000000'
-- ProjectID (upload1):             '00000000-0000-0000-0000-000000000001'
-- AuthTokenID(user1->upload1):     '00000000-0000-0000-0000-000000000002'
-- SecretID(SECRET_ENV):            '00000000-0000-0000-0000-000000000003'
-------------------------------------------------------------------------

INSERT INTO "user"(id, github_id, avatar_url, name, email, github_api_token, username)
VALUES('00000000-0000-0000-0000-000000000000', 1, 'avatar', 'name1', 'user1@email.com', 'token', 'user1');

INSERT INTO project(name, type, id)
VALUES('upload1', 'upload', '00000000-0000-0000-0000-000000000001');

INSERT INTO collaborator(project_id, user_id, role)
VALUES('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000000', 'Owner');

INSERT INTO auth_token(project_id, id, description, scope_push, scope_pull)
VALUES('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'asd', true, true);

INSERT INTO secret(project_id, id, name, value)
VALUES('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'SECRET_ENV', 'hello world');
