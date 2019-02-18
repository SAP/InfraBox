CREATE TABLE sshkey (
    project_id uuid NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(255) NOT NULL,
    secret_id uuid NOT NULL
);

ALTER TABLE ONLY sshkey
    ADD CONSTRAINT sshkey_pkey PRIMARY KEY (id);
