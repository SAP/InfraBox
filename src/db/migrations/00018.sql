ALTER TABLE leader_election DROP CONSTRAINT keader_election_pkey;
ALTER TABLE leader_election ADD COLUMN cluster_name character varying DEFAULT 'master';
ALTER TABLE leader_election ADD PRIMARY KEY (service_name);
