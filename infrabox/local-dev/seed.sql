INSERT INTO cluster (name, active, labels, root_url, nodes, cpu_capacity, memory_capacity)
VALUES ('master', true, '{master,default}', 'http://localhost:8090', 1, 10, 10000);

-- Default admin user: admin@local.dev / admin123
INSERT INTO "user" (username, email, password, role)
VALUES ('admin', 'admin@local.dev', '$2b$12$QxG47fCe3dqJQCjx6Z5vy./jM7/o8cZFeudhTTfcoII0IE0PmY10m', 'admin');

-- Regular users: password123
INSERT INTO "user" (id, username, email, password, role) VALUES
  ('aaaaaaaa-0001-0001-0001-aaaaaaaaaaaa', 'alice', 'alice@local.dev', '$2b$12$oi46ZRkcmGP4A8klhxe0reHN0FBn8.N7dupNhcjP.2S6nZjlpauzq', 'user'),
  ('aaaaaaaa-0002-0002-0002-aaaaaaaaaaaa', 'bob',   'bob@local.dev',   '$2b$12$oi46ZRkcmGP4A8klhxe0reHN0FBn8.N7dupNhcjP.2S6nZjlpauzq', 'user');

-- Sample projects
INSERT INTO project (id, name, type) VALUES
  ('bbbbbbbb-0001-0001-0001-bbbbbbbbbbbb', 'project-alpha', 'upload'),
  ('bbbbbbbb-0002-0002-0002-bbbbbbbbbbbb', 'project-beta',  'upload'),
  ('bbbbbbbb-0003-0003-0003-bbbbbbbbbbbb', 'project-gamma', 'upload');

-- alice: Owner on alpha, Developer on beta; no access to gamma
INSERT INTO collaborator (user_id, project_id, role) VALUES
  ('aaaaaaaa-0001-0001-0001-aaaaaaaaaaaa', 'bbbbbbbb-0001-0001-0001-bbbbbbbbbbbb', 'Owner'),
  ('aaaaaaaa-0001-0001-0001-aaaaaaaaaaaa', 'bbbbbbbb-0002-0002-0002-bbbbbbbbbbbb', 'Developer');
