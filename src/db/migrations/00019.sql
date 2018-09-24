CREATE TYPE user_role AS ENUM (
    'Developer',
    'Administrator',
    'Owner'
);

ALTER TABLE collaborator ADD COLUMN role user_role DEFAULT 'Developer' NOT NULL;
UPDATE collaborator SET role = 'Owner' WHERE owner = true;

ALTER TABLE collaborator DROP COLUMN owner CASCADE;