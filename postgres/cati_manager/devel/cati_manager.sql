CREATE TABLE column_properties (
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    properties JSONB,
    PRIMARY KEY (table_name, column_name));

CREATE TABLE identity ( 
    login TEXT PRIMARY KEY, 
    password BYTEA, 
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    institution TEXT,
    registration_time TIMESTAMP,
    email_verification_time TIMESTAMP);
INSERT INTO column_properties VALUES ('identity', 'password', '{"html_type": "password", "double_check": true}');
INSERT INTO column_properties VALUES ('identity', 'email', '{"html_type": "email"}');
INSERT INTO column_properties VALUES ('identity', 'first_name', '{"label": "first name"}');
INSERT INTO column_properties VALUES ('identity', 'last_name', '{"label": "last name"}');
INSERT INTO column_properties VALUES ('identity', 'registration_time', '{"visible": false}');
INSERT INTO column_properties VALUES ('identity', 'email_verification_time', '{"visible": false}');

INSERT INTO identity ( login, registration_time ) VALUES ( 'cati_manager', now() ); 

CREATE FUNCTION create_identity_role() RETURNS trigger AS $$
DECLARE
    salt BYTEA;
    pwd BYTEA;
BEGIN
    IF NEW.registration_time IS NULL THEN
        NEW.registration_time = now();
    END IF;
    salt := substring(random()::text from 2);
    pwd := public.digest(NEW.password || salt, 'sha256');
    NEW.password := pwd || salt;
    EXECUTE 'CREATE ROLE ' || quote_ident('cati_manager$' || NEW.login) || ' LOGIN ENCRYPTED PASSWORD ' || quote_literal(encode(NEW.password,'base64')) || ';';
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

CREATE TABLE project (
    id TEXT PRIMARY KEY NOT NULL, 
    name TEXT,
    description TEXT,
    authority TEXT REFERENCES identity );

    
CREATE TABLE credential (
    project TEXT REFERENCES project NOT NULL, 
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
    login TEXT REFERENCES identity NOT NULL,
    authority TEXT REFERENCES identity, 
    authorization_time TIMESTAMP, 
    FOREIGN KEY (project, credential) REFERENCES credential,
    PRIMARY KEY (project, credential, login) );

CREATE FUNCTION create_granting() RETURNS trigger AS $$
BEGIN
    IF NEW.authority IS NULL THEN
        NEW.authority = CURRENT_USER;
    END IF;
    IF NEW.authorization_time IS NULL THEN
        NEW.authorization_time = now();
    END IF;
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


INSERT INTO project (id, name, description, authority) VALUES ('cati_manager', 'CATI manager', 'Management of users and authorizations for all CATI studies and projects', 'cati_manager');
INSERT INTO credential (project, id, name, description) VALUES ('cati_manager', 'server_admin', 'server administrator', 'A server administrator can put the server in maintenane mode and update the database schema and the software.');
INSERT INTO credential (project, id, name, description) VALUES ('cati_manager', 'user_moderator', 'user moderator', 'A user moderator can validate and invalidate user account.');
GRANT USAGE ON SCHEMA cati_manager TO cati_manager$user_moderator;
GRANT SELECT, UPDATE, DELETE ON TABLE cati_manager.identity TO cati_manager$user_moderator;
GRANT SELECT ON TABLE cati_manager.identity_not_validated TO cati_manager$user_moderator;
GRANT SELECT ON TABLE cati_manager.identity_email_not_verified TO cati_manager$user_moderator;
GRANT SELECT, INSERT ON TABLE cati_manager.granting TO cati_manager$user_moderator;
INSERT INTO credential (project, id, name, description) VALUES ('cati_manager', 'valid_user', 'valid user', 'A user with this credential has been validated by a user moderator. Without this credential, a user cannot do anything.');
