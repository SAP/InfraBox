alter type job_type rename to job_type__;

CREATE TYPE job_type AS ENUM (
    'create_job_matrix',
    'run_project_container',
    'run_docker_compose',
    'knative_build',
    'wait'
);

-- alter all you enum columns
alter table job
  alter column type type job_type using type::text::job_type;

-- drop the old enum
drop type job_type__;
