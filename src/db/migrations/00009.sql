ALTER TABLE job ADD COLUMN cluster_name character varying;
ALTER TABLE job ADD COLUMN archive jsonb[];

CREATE TABLE cluster
(
      name character varying NOT NULL,
      active boolean NOT NULL,
      labels character varying[] NOT NULL,
      root_url character varying NOT NULL,
      nodes integer NOT NULL,
      cpu_capacity integer NOT NULL,
      memory_capacity integer NOT NULL,
      CONSTRAINT cluster_pkey PRIMARY KEY (name)
);
