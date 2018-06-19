-- cati_manager changeset : base
CREATE EXTENSION pgcrypto;
CREATE LANGUAGE plpython3u;

CREATE SCHEMA cati_manager;

SET search_path = cati_manager, public;

CREATE TABLE column_properties
(
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    properties JSONB,
    PRIMARY KEY (table_name, column_name)
);

-- CREATE TYPE log_action AS ENUM ('insert', 'update', 'delete');
-- 
-- CREATE TABLE log
-- (
--     time TIMESTAMP NOT NULL,
--     pg_schema TEXT NOT NULL,
--     pg_table TEXT NOT NULL,
--     action table_action,
--     project TEXT REFERENCES project,
--     item_id TEXT NOT NULL
-- );


CREATE TABLE identity
( 
    login TEXT PRIMARY KEY, 
    password BYTEA, 
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    institution TEXT,
    registration_time TIMESTAMP,
    email_verification_time TIMESTAMP
);
INSERT INTO column_properties VALUES ('identity', 'password', '{"html_type": "password", "double_check": true}');
INSERT INTO column_properties VALUES ('identity', 'email', '{"html_type": "email"}');
INSERT INTO column_properties VALUES ('identity', 'first_name', '{"label": "first name"}');
INSERT INTO column_properties VALUES ('identity', 'last_name', '{"label": "last name"}');
INSERT INTO column_properties VALUES ('identity', 'registration_time', '{"visible": false}');
INSERT INTO column_properties VALUES ('identity', 'email_verification_time', '{"visible": false}');

INSERT INTO identity ( login, registration_time ) VALUES ( 'cati_manager', now() ); 

CREATE TABLE pgp_public_keys ( name VARCHAR NOT NULL PRIMARY KEY, pgp_key BYTEA );

CREATE FUNCTION create_identity_role() RETURNS trigger AS $$
DECLARE
    salt BYTEA;
    pwd BYTEA;
    key_var BYTEA;
BEGIN
    IF NEW.registration_time IS NULL THEN
        NEW.registration_time = now();
    END IF;
    SELECT pgp_key FROM cati_manager.pgp_public_keys INTO STRICT key_var WHERE name = 'cati_manager';
    salt := substring(gen_salt('bf'),8);
    pwd := NEW.password;
    NEW.password := pgp_pub_encrypt_bytea(NEW.password || salt, key_var);
    EXECUTE 'CREATE ROLE ' || quote_ident('cati_manager$' || NEW.login) || ' LOGIN PASSWORD ' || quote_literal(convert_from(pwd,'UTF8')) || ';';
    RETURN NEW;
END $$ LANGUAGE plpgsql
SECURITY DEFINER;
REVOKE ALL ON FUNCTION create_identity_role() FROM PUBLIC;
CREATE TRIGGER create_identity_role BEFORE INSERT ON identity FOR EACH ROW EXECUTE PROCEDURE create_identity_role();

CREATE OR REPLACE FUNCTION delete_identity_role() RETURNS trigger AS $$
BEGIN
--     EXECUTE 'REVOKE ' || quote_ident(OLD.login) || ' FROM cati_manager;';
--     EXECUTE 'REASSIGN OWNED BY ' || quote_ident(OLD.login) || ' TO CURRENT_USER;';
--     EXECUTE 'DROP OWNED BY ' || quote_ident(OLD.login) || ';';
    EXECUTE 'DROP ROLE ' || quote_ident('cati_manager$' || OLD.login) || ';';
    RETURN OLD;
END $$ LANGUAGE plpgsql
SECURITY DEFINER;
REVOKE ALL ON FUNCTION delete_identity_role() FROM PUBLIC;
CREATE TRIGGER delete_identity_role BEFORE DELETE ON identity FOR EACH ROW EXECUTE PROCEDURE delete_identity_role();



CREATE TABLE software_component (
    id TEXT PRIMARY KEY NOT NULL, 
    name TEXT,
    description TEXT,
    git_url TEXT,
    installed_version TEXT );

CREATE TABLE project_module (
    id TEXT PRIMARY KEY NOT NULL, 
    name TEXT,
    description TEXT,
    module TEXT,
    component TEXT REFERENCES software_component ON UPDATE CASCADE );

CREATE TABLE project (
    id TEXT PRIMARY KEY NOT NULL, 
    name TEXT,
    description TEXT,
    module TEXT REFERENCES project_module ON UPDATE CASCADE );

INSERT INTO project (id, name, description) VALUES ('cati_manager', 'CATI manager', 'Management of users and authorizations for all CATI studies and projects');


    

CREATE TABLE credential (
    project TEXT  NOT NULL REFERENCES project ON UPDATE CASCADE, 
    id TEXT NOT NULL, 
    name TEXT, 
    description TEXT, 
    PRIMARY KEY ( project, id ) );

CREATE FUNCTION create_credential() RETURNS trigger AS $$
BEGIN
    EXECUTE 'CREATE ROLE ' || quote_ident(NEW.project || '$' || NEW.id) || ' NOLOGIN;';
    RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER create_credential BEFORE INSERT ON credential FOR EACH ROW EXECUTE PROCEDURE create_credential();


CREATE TABLE granting ( 
    project TEXT NOT NULL, 
    credential TEXT NOT NULL,
    login TEXT NOT NULL REFERENCES identity ON UPDATE CASCADE,
    FOREIGN KEY (project, credential) REFERENCES credential ON UPDATE CASCADE,
    PRIMARY KEY (project, credential, login) );

CREATE FUNCTION create_granting() RETURNS trigger AS $$
BEGIN
    EXECUTE 'GRANT ' || quote_ident(NEW.project || '$' || NEW.credential) || ' TO ' || quote_ident('cati_manager$' || NEW.login) || ';';
    RETURN NEW;
END $$ LANGUAGE plpgsql
SECURITY DEFINER;
REVOKE ALL ON FUNCTION create_granting() FROM PUBLIC;
CREATE TRIGGER create_granting BEFORE INSERT ON granting FOR EACH ROW EXECUTE PROCEDURE create_granting();

CREATE VIEW identity_email_not_verified AS
    SELECT *, md5(login || 
                    coalesce(first_name,'') || 
                    coalesce(last_name,'') || 
                    coalesce(email,'') || 
                    coalesce(registration_time::text, '')) secret
    FROM cati_manager.identity
    WHERE login != 'cati_manager' AND
        email_verification_time IS NULL;

CREATE VIEW identity_not_validated AS 
    SELECT *
    FROM cati_manager.identity i
    WHERE i.login != 'cati_manager' AND
        i.email_verification_time IS NOT NULL AND
        i.login NOT IN
        (SELECT login 
            FROM cati_manager.granting g 
            WHERE g.project = 'cati_manager' AND 
                g.credential = 'valid_user');

-- This view returns all the projects for which the current_user has at least 
-- one credential
CREATE VIEW my_projects AS
    SELECT * FROM project
    WHERE id IN
    (SELECT g.project
        FROM granting g);

INSERT INTO credential (project, id, name, description) VALUES ('cati_manager', 'server_admin', 'server administrator', 'A server administrator can put the server in maintenane mode and update the database schema and the software.');
INSERT INTO credential (project, id, name, description) VALUES ('cati_manager', 'user_moderator', 'user moderator', 'A user moderator can validate and invalidate user accounts.');
GRANT USAGE ON SCHEMA cati_manager TO cati_manager$server_admin, cati_manager$user_moderator;
GRANT SELECT, UPDATE, DELETE ON TABLE cati_manager.identity TO cati_manager$server_admin, cati_manager$user_moderator;
GRANT SELECT ON TABLE cati_manager.project TO PUBLIC;
GRANT SELECT ON TABLE cati_manager.my_projects TO PUBLIC;
GRANT SELECT ON TABLE cati_manager.credential TO PUBLIC;
GRANT SELECT ON granting TO PUBLIC;
ALTER TABLE granting ENABLE ROW LEVEL SECURITY;
    CREATE POLICY my_grants 
    ON granting USING (current_user = 'cati_manager$' || login); 
GRANT SELECT ON TABLE cati_manager.identity_not_validated TO cati_manager$user_moderator;
GRANT SELECT ON TABLE cati_manager.identity_email_not_verified TO cati_manager$user_moderator;
GRANT SELECT, INSERT ON TABLE cati_manager.granting TO cati_manager$user_moderator;
INSERT INTO credential (project, id, name, description) VALUES ('cati_manager', 'valid_user', 'valid user', 'A user with this credential has been validated by a user moderator. Without this credential, a user cannot do anything.');



CREATE TABLE study_template 
(
    id VARCHAR NOT NULL PRIMARY KEY,
    python_module VARCHAR,
    description VARCHAR
);

INSERT INTO study_template (id, python_module, description)
    VALUES ('cati', 'cati_manager.study_template.cati', 'Standard historical CATI organisation of studies');

CREATE TABLE study
(
    id VARCHAR NOT NULL PRIMARY KEY,
    label VARCHAR,
    description VARCHAR,
    template VARCHAR REFERENCES study_template ON UPDATE CASCADE,
    properties JSONB
);
