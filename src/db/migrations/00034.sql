CREATE TYPE user_role AS ENUM (
    'user',
    'devops',
    'admin'
);

ALTER TABLE user ADD COLUMN role user_role DEFAULT 'user';
