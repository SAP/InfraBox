CREATE TABLE vault (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    url VARCHAR NOT NULL,
    token VARCHAR NOT NULL
);

CREATE INDEX vault_project_id_idx ON vault USING btree (project_id);
