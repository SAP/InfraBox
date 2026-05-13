INSERT INTO cluster (name, active, labels, root_url, nodes, cpu_capacity, memory_capacity)
VALUES ('master', true, '{master,default}', 'http://localhost:8090', 1, 10, 10000);

-- Default admin user: admin@local.dev / admin123
INSERT INTO "user" (username, email, password, role)
VALUES ('admin', 'admin@local.dev', '$2b$12$QxG47fCe3dqJQCjx6Z5vy./jM7/o8cZFeudhTTfcoII0IE0PmY10m', 'admin');
