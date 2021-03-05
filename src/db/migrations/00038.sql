DROP TABLE vault;

CREATE TABLE vault (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    name VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    version VARCHAR NOT NULL,
    token VARCHAR NOT NULL,
    cert TEXT,
    UNIQUE(project_id,name)
);
