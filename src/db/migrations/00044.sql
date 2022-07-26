ALTER TABLE "project" DROP COLUMN build_skip_pattern;
CREATE TABLE "project_skip_pattern" (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    skip_pattern TEXT,
    UNIQUE(project_id)
);
