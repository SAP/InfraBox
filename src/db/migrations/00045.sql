CREATE TABLE "global_token" (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    description VARCHAR(255) NOT NULL,
    scope_push BOOLEAN DEFAULT FALSE NOT NULL,
    scope_pull BOOLEAN DEFAULT TRUE NOT NULL,
    PRIMARY KEY (id)
);