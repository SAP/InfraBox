ALTER TABLE job ADD COLUMN restarted boolean default false;
-- Drop table

-- DROP TABLE public.quotas

CREATE TABLE public.quotas (
	value int4 NOT NULL,
	object_id varchar(255) NOT NULL,
	"name" varchar(255) NOT NULL,
	id uuid NOT NULL DEFAULT gen_random_uuid(),
	description varchar NULL,
	object_type varchar NOT NULL
);

INSERT INTO public.quotas (value,object_id,"name",id,description,object_type) VALUES 
(50,'default_value_project','max_secret_project','dcad196c-6db8-4bd9-8981-40065208046f','Max secret in a project','project')
,(50,'default_value_project','max_collaborator_project','ecebcd79-8b61-47be-a9dc-744a745a684f','Not yet implemented','project')
,(50,'default_value_user','max_project_user','9bc4535f-c625-4333-91a0-28123352b243','max_project_user','user')
,(100,'default_value','max_cpu_job','7c5711a6-51a0-4542-bc6b-7b8276e6dcda','Max CPU wich a single job can have','project')
,(100,'default_value','max_runningjob_build','a421c213-0742-4995-8ff3-120b394525ce','Not yet implemented','project')
,(100,'default_value','max_memory_job','781cdb24-7766-4b54-adc0-e616a276865a','Not yet implemented','project')
,(100,'default_value','max_timeout_job','fe7044dd-b03e-413b-8c13-627d7d952add','Not yet implemented','project')
,(100,'default_value_project','max_runningbuild_project','d692755c-71e7-402c-825f-b26dbf260cca','Not yet implemented','project')
,(100,'default_value_project','max_runningjob_project','f5448b68-b18f-4274-b9ac-d9a4e3ce6977','Not yet implemented','project')
;