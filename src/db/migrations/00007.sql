CREATE TABLE public.leader_election
(
  service_name character varying(128) NOT NULL,
  last_seen_active timestamp without time zone NOT NULL DEFAULT now(),
  CONSTRAINT keader_election_pkey PRIMARY KEY (service_name)
)
