CREATE TYPE system_role AS ENUM (
    'user',
    'devops',
    'admin'
);

ALTER TABLE "user" ADD COLUMN role system_role DEFAULT 'user' NOT NULL;
UPDATE "user" SET role = 'admin' WHERE id = '00000000-0000-0000-0000-000000000000';
