ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_email_index UNIQUE (email);

UPDATE "user" SET email = lower(email);
