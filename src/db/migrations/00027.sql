CREATE TABLE cronjob (
    project_id uuid NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(255) NOT NULL,
    minute character varying(255) NOT NULL,
    hour character varying(255) NOT NULL,
    day_month character varying(255) NOT NULL,
    month character varying(255) NOT NULL,
    day_week character varying(255) NOT NULL,
    sha character varying(255) NOT NULL,
    last_trigger timestamp without time zone DEFAULT now() NOT NULL
);

ALTER TABLE ONLY cronjob
    ADD CONSTRAINT cronjob_pkey PRIMARY KEY (id);
