--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.5
-- Dumped by pg_dump version 9.5.8

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: test_db; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE test_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';


\connect test_db

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET search_path = public, pg_catalog;

--
-- Name: job_state; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE job_state AS ENUM (
    'queued',
    'scheduled',
    'running',
    'finished',
    'failure',
    'error',
    'skipped',
    'killed'
);


--
-- Name: job_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE job_type AS ENUM (
    'create_job_matrix',
    'run_project_container',
    'run_docker_compose',
    'wait',
    'test'
);


--
-- Name: markup_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE markup_type AS ENUM (
    'markup',
    'markdown'
);


--
-- Name: project_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE project_type AS ENUM (
    'github',
    'upload',
    'test',
    'gerrit'
);


--
-- Name: test_result; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE test_result AS ENUM (
    'ok',
    'failure',
    'error',
    'skipped'
);


--
-- Name: console_notify(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION console_notify() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
BEGIN
  IF TG_OP = 'DELETE' THEN
    RETURN OLD;
  END IF;

  IF TG_OP = 'UPDATE' THEN
    RETURN NEW;
  END IF;

  PERFORM pg_notify('console_update', json_build_object('id', NEW.id, 'job_id', NEW.job_id)::text);

  RETURN NEW;
END;
$$;


--
-- Name: job_queue_notify(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION job_queue_notify() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
	build_json json;
	project_json json;
	job_json json;
	commit_json json;
	data_json json;
	pull_request_json json;
	project project%ROWTYPE;
BEGIN
	IF TG_OP = 'DELETE' THEN
		RETURN OLD;
	END IF;

	-- create build json
	SELECT json_build_object(
		'id', b.id,
		'build_number', b.build_number,
		'restart_counter', b.restart_counter
	) INTO build_json FROM build b WHERE id = NEW.build_id;

	-- create project json
	SELECT json_build_object(
		'id', p.id,
		'name', p.name,
		'type', p.type
	) INTO project_json FROM project p WHERE id = NEW.project_id;

	-- create job json
	job_json := json_build_object(
		'id', NEW.id,
		'state', NEW.state,
		'start_date', NEW.start_date,
		'type', NEW.type,
		'dockerfile', NEW.dockerfile,
		'end_date', NEW.end_date,
		'name', NEW.name,
		'cpu', NEW.cpu,
		'memory', NEW.memory,
		'dependencies', NEW.dependencies,
		'created_at', NEW.created_at
	);


	SELECT * INTO project FROM project WHERE id = NEW.project_id;
	IF project.type in ('github', 'gerrit') THEN
		-- create commit json
		SELECT json_build_object(
			'id', c.id,
			'message', split_part(c.message, '\n', 1),
			'author_name', c.author_name,
			'author_email', c.author_email,
			'author_username', c.author_username,
			'committer_name', c.committer_name,
			'committer_email', c.committer_email,
			'committer_username', c.committer_username,
			'committer_avatar_url', u.avatar_url,
			'url', c.url,
			'branch', c.branch
		), json_build_object(
			'title', pr.title,
			'url', pr.url
		) INTO commit_json, pull_request_json
		FROM job j
		INNER JOIN build b
			ON j.build_id = b.id
		INNER JOIN commit c
			ON b.commit_id = c.id
		LEFT OUTER JOIN "user" u
			ON c.committer_username = u.username
		LEFT OUTER JOIN pull_request pr
			ON c.pull_request_id = pr.id
		WHERE b.id = NEW.build_id AND j.id = NEW.id;
	END IF;

	data_json := json_build_object('job', job_json, 'build', build_json, 'project', project_json, 'commit', commit_json, 'pull_request', pull_request_json);
	PERFORM pg_notify('job_update', json_build_object('type', TG_OP, 'data', data_json)::text);

  RETURN NEW;
END;
$$;


--
-- Name: truncate_tables(character varying); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION truncate_tables(username character varying) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    statements CURSOR FOR
        SELECT tablename FROM pg_tables
        WHERE tableowner = username AND schemaname = 'public';
BEGIN
    FOR stmt IN statements LOOP
        EXECUTE 'TRUNCATE TABLE ' || quote_ident(stmt.tablename) || ' CASCADE;';
    END LOOP;
END;
$$;


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: abort; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE abort (
    job_id uuid NOT NULL
);


--
-- Name: auth_token; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE auth_token (
    token uuid DEFAULT gen_random_uuid() NOT NULL,
    description character varying(255) NOT NULL,
    user_id uuid NOT NULL,
    scope_push boolean DEFAULT false NOT NULL,
    scope_pull boolean DEFAULT false NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL
);


--
-- Name: build; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE build (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    commit_id character varying(255),
    build_number integer NOT NULL,
    project_id uuid NOT NULL,
    restart_counter integer DEFAULT 1 NOT NULL,
    source_upload_id uuid
);


--
-- Name: collaborator; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE collaborator (
    user_id uuid NOT NULL,
    project_id uuid NOT NULL,
    owner boolean DEFAULT false NOT NULL
);


--
-- Name: commit; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE commit (
    id character varying(255) NOT NULL,
    message character varying(4096),
    repository_id uuid NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    author_name character varying NOT NULL,
    author_email character varying NOT NULL,
    author_username character varying,
    committer_name character varying NOT NULL,
    committer_email character varying NOT NULL,
    committer_username character varying,
    url character varying NOT NULL,
    branch character varying NOT NULL,
    project_id uuid,
    tag character varying(255),
    pull_request_id uuid
);

--
-- Name: console; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE console (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_id uuid NOT NULL,
    output text NOT NULL,
    date timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: job; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE job (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    state job_state NOT NULL,
    start_date timestamp with time zone,
    build_id uuid NOT NULL,
    console text,
    type job_type NOT NULL,
    dockerfile character varying(255),
    end_date timestamp with time zone,
    name character varying(50) NOT NULL,
    project_id uuid NOT NULL,
    dependencies jsonb,
    build_only boolean NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    keep boolean DEFAULT false NOT NULL,
    repo jsonb,
    base_path character varying(1024),
    scan_container boolean DEFAULT false NOT NULL,
    stats text,
    env_var jsonb,
    env_var_ref jsonb,
    cpu integer DEFAULT 1 NOT NULL,
    memory integer DEFAULT 1024 NOT NULL,
    build_arg jsonb,
    deployment jsonb,
    download jsonb
);


--
-- Name: job_badge; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE job_badge (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_id uuid NOT NULL,
    subject character varying(32) NOT NULL,
    status character varying(32) NOT NULL,
    color character varying(32) NOT NULL,
    project_id uuid NOT NULL
);


--
-- Name: job_markup; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE job_markup (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    job_id uuid NOT NULL,
    name character varying(255),
    data text NOT NULL,
    project_id uuid NOT NULL,
    type markup_type NOT NULL
);


--
-- Name: job_stat; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE job_stat (
    job_id uuid NOT NULL,
    tests_added integer DEFAULT 0 NOT NULL,
    tests_duration double precision NOT NULL,
    tests_skipped integer DEFAULT 0 NOT NULL,
    tests_failed integer DEFAULT 0 NOT NULL,
    tests_error integer DEFAULT 0 NOT NULL,
    tests_passed integer DEFAULT 0 NOT NULL,
    project_id uuid NOT NULL
);


--
-- Name: measurement; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE measurement (
    test_run_id uuid NOT NULL,
    name character varying(32) NOT NULL,
    value double precision NOT NULL,
    unit character varying(32) NOT NULL,
    project_id uuid NOT NULL
);


--
-- Name: project; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE project (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(255) NOT NULL,
    type project_type NOT NULL,
    public boolean DEFAULT false NOT NULL
);


--
-- Name: pull_request; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE pull_request (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    github_pull_request_id integer NOT NULL,
    url character varying NOT NULL
);


--
-- Name: repository; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE repository (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(255) NOT NULL,
    html_url character varying(255) NOT NULL,
    clone_url character varying(255) NOT NULL,
    github_id integer NOT NULL,
    github_hook_id integer,
    project_id uuid NOT NULL,
    private boolean NOT NULL
);


--
-- Name: secret; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE secret (
    project_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    value character varying(8192) NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL
);


--
-- Name: source_upload; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE source_upload (
    project_id uuid NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    filename character varying(255) NOT NULL,
    filesize bigint NOT NULL
);


--
-- Name: test; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE test (
    name character varying(255) NOT NULL,
    project_id uuid NOT NULL,
    suite character varying(255) NOT NULL,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    build_number integer DEFAULT 0 NOT NULL
);


--
-- Name: test_run; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE test_run (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    test_id uuid NOT NULL,
    job_id uuid NOT NULL,
    state test_result NOT NULL,
    duration double precision NOT NULL,
    project_id uuid NOT NULL,
    message text,
    stack text
);


--
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE "user" (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    github_id integer,
    username character varying(255),
    avatar_url character varying(255),
    name character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    email character varying(255),
    github_api_token character varying,
    password character varying(255)
);


--
-- Name: user_quota; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE user_quota (
    user_id uuid NOT NULL,
    max_concurrent_jobs integer NOT NULL,
    max_cpu_per_job integer NOT NULL,
    max_memory_per_job integer NOT NULL,
    max_jobs_per_build integer NOT NULL
);


--
-- Name: auth_token_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY auth_token
    ADD CONSTRAINT auth_token_pkey PRIMARY KEY (token);


--
-- Name: build_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY build
    ADD CONSTRAINT build_pkey PRIMARY KEY (id);


--
-- Name: build_project_id_build_number_restart_counter_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY build
    ADD CONSTRAINT build_project_id_build_number_restart_counter_key UNIQUE (project_id, build_number, restart_counter);


--
-- Name: collaborator_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY collaborator
    ADD CONSTRAINT collaborator_pkey PRIMARY KEY (user_id, project_id);


--
-- Name: commit_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY commit
    ADD CONSTRAINT commit_pkey PRIMARY KEY (repository_id, id);


--
-- Name: console_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY console
    ADD CONSTRAINT console_pkey PRIMARY KEY (id);


--
-- Name: job_markdown_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY job_markup
    ADD CONSTRAINT job_markdown_pkey PRIMARY KEY (id);


--
-- Name: job_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY job
    ADD CONSTRAINT job_pkey PRIMARY KEY (id);


--
-- Name: job_stat_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY job_stat
    ADD CONSTRAINT job_stat_pkey PRIMARY KEY (job_id);


--
-- Name: project_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY project
    ADD CONSTRAINT project_pkey PRIMARY KEY (id);


--
-- Name: pull_request_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY pull_request
    ADD CONSTRAINT pull_request_pkey PRIMARY KEY (id);


--
-- Name: repository_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY repository
    ADD CONSTRAINT repository_pkey PRIMARY KEY (id);


--
-- Name: secret_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY secret
    ADD CONSTRAINT secret_pkey PRIMARY KEY (id);


--
-- Name: source_upload_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY source_upload
    ADD CONSTRAINT source_upload_pkey PRIMARY KEY (id);


--
-- Name: test_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY test
    ADD CONSTRAINT test_pkey PRIMARY KEY (id);


--
-- Name: test_run_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY test_run
    ADD CONSTRAINT test_run_pkey PRIMARY KEY (id);


--
-- Name: user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user_quota_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY user_quota
    ADD CONSTRAINT user_quota_pkey PRIMARY KEY (user_id);


--
-- Name: auth_token_user_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX auth_token_user_id_idx ON auth_token USING btree (user_id);


--
-- Name: build_project_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX build_project_id_idx ON build USING btree (project_id);


--
-- Name: collaborator_project_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX collaborator_project_id_idx ON collaborator USING btree (project_id);


--
-- Name: collaborator_user_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX collaborator_user_id_idx ON collaborator USING btree (user_id);


--
-- Name: job_badge_job_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX job_badge_job_id_idx ON job_badge USING btree (job_id);


--
-- Name: job_markdown_project_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX job_markdown_project_id_idx ON job_markup USING btree (project_id);


--
-- Name: job_project_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX job_project_id_idx ON job USING btree (project_id);


--
-- Name: measurement_project_id_test_run_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX measurement_project_id_test_run_id_idx ON measurement USING btree (project_id, test_run_id);


--
-- Name: pull_request_project_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX pull_request_project_id_idx ON pull_request USING btree (project_id);


--
-- Name: secret_project_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX secret_project_id_idx ON secret USING btree (project_id);


--
-- Name: source_upload_project_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX source_upload_project_id_idx ON source_upload USING btree (project_id);


--
-- Name: test_project_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX test_project_id_idx ON test USING btree (project_id);


--
-- Name: test_run_job_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX test_run_job_id_idx ON test_run USING btree (job_id);


--
-- Name: test_run_project_id_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX test_run_project_id_idx ON test_run USING btree (project_id);


--
-- Name: console_notify_insert; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER console_notify_insert AFTER INSERT ON console FOR EACH ROW EXECUTE PROCEDURE console_notify();


--
-- Name: job_queue_notify_insert; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER job_queue_notify_insert AFTER INSERT ON job FOR EACH ROW EXECUTE PROCEDURE job_queue_notify();


--
-- Name: job_queue_notify_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER job_queue_notify_update AFTER UPDATE ON job FOR EACH ROW EXECUTE PROCEDURE job_queue_notify();


--
-- Name: public; Type: ACL; Schema: -; Owner: -
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

