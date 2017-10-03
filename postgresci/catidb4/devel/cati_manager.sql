CREATE TABLE column_properties (
    table_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    properties JSONB,
    PRIMARY KEY (table_name, column_name));

CREATE TABLE identity ( 
    login TEXT PRIMARY KEY, 
    password TEXT, 
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    institution TEXT,
    registration_time TIMESTAMP );
INSERT INTO column_properties VALUES ('identity', 'first_name', '{"label": "first name"}');
INSERT INTO column_properties VALUES ('identity', 'last_name', '{"label": "last name"}');
INSERT INTO column_properties VALUES ('identity', 'password', '{"double_check": true}');
INSERT INTO column_properties VALUES ('identity', 'registration_time', '{"visible": false}');

INSERT INTO identity ( login, registration_time ) VALUES ( 'cati_manager', now() ); 
GRANT postgresci TO cati_manager;

CREATE FUNCTION create_identity_role() RETURNS trigger AS $$
BEGIN
    IF NEW.registration_time IS NULL THEN
        NEW.registration_time = now();
    END IF;
    EXECUTE 'CREATE ROLE ' || quote_ident(NEW.login) || ' LOGIN ENCRYPTED PASSWORD ' || quote_nullable(NEW.password) || ';';
    EXECUTE 'GRANT ' || quote_ident(NEW.login) || ' TO cati_manager;';
    RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER create_identity_role BEFORE INSERT ON identity FOR EACH ROW EXECUTE PROCEDURE create_identity_role();

CREATE OR REPLACE FUNCTION delete_identity_role() RETURNS trigger AS $$
BEGIN
    EXECUTE 'REVOKE ' || quote_ident(OLD.login) || ' FROM cati_manager;';
    EXECUTE 'REASSIGN OWNED BY ' || quote_ident(OLD.login) || ' TO CURRENT_USER;';
    EXECUTE 'DROP OWNED BY ' || quote_ident(OLD.login) || ';';
    EXECUTE 'DROP ROLE ' || quote_ident(OLD.login) || ';';
    RETURN NEW;
END $$ LANGUAGE plpgsql;
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
    EXECUTE 'GRANT ' || quote_ident(NEW.project || '$' || NEW.credential) || ' TO ' || quote_ident(NEW.login) || ';';
    RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER create_granting BEFORE INSERT ON granting FOR EACH ROW EXECUTE PROCEDURE create_granting();

INSERT INTO project (id, name, description, authority) VALUES ('cati_manager', 'CATI manager', 'Management of users and authorizations for all CATI studies and projects', 'cati_manager');
INSERT INTO credential (project, id, name, description) VALUES ('cati_manager', 'user_moderator', 'user moderator', 'A user moderator can validate and invalidate user account.');
INSERT INTO credential (project, id, name, description) VALUES ('cati_manager', 'valid_user', 'valid user', 'A user with this credential has been validated by a user moderator. Without this credential, a user cannot do anything.');

-- CREATE FUNCTION create_credential_role() RETURNS trigger AS $$
-- BEGIN
--     EXECUTE 'CREATE ROLE ' || quote_ident(NEW.id) || ' NOLOGIN;';
--     RETURN NEW;
-- END $$ LANGUAGE plpgsql;
-- CREATE TRIGGER create_credential_role BEFORE INSERT ON credential FOR EACH ROW EXECUTE PROCEDURE create_credential_role();
-- 
-- CREATE FUNCTION delete_credential_role() RETURNS trigger AS $$
-- BEGIN
--     EXECUTE 'REASSIGN OWNED BY ' || quote_ident(OLD.id) || ' TO CURRENT_USER;';
--     EXECUTE 'DROP OWNED BY ' || quote_ident(OLD.id) || ';';
--     EXECUTE 'DROP ROLE ' || quote_ident(OLD.id) || ';';
--     RETURN OLD;
-- END $$ LANGUAGE plpgsql;
-- CREATE TRIGGER delete_credential_role BEFORE DELETE ON credential FOR EACH ROW EXECUTE PROCEDURE delete_credential_role();
