
CREATE TABLE identity ( 
    login TEXT PRIMARY KEY, 
    password TEXT, 
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    authority TEXT REFERENCES identity,
    authorization_time TIMESTAMP );
INSERT INTO identity ( login, authorization_time ) VALUES ( 'cati_manager', now() ); 

CREATE FUNCTION create_identity_role() RETURNS trigger AS $$
BEGIN
    IF NEW.authority IS NULL THEN
        NEW.authority = CURRENT_USER;
    END IF;
    IF NEW.authorization_time IS NULL THEN
        NEW.authorization_time = now();
    END IF;
    EXECUTE 'CREATE ROLE ' || quote_ident(NEW.login) || ' LOGIN ENCRYPTED PASSWORD ' || quote_nullable(NEW.password) || ';';
    EXECUTE 'GRANT ' || quote_ident(NEW.login) || ' TO cati_manager;';
    EXECUTE 'GRANT postgresci TO ' || quote_ident(NEW.login) || ';';
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
    description TEXT );
CREATE TABLE credential (
    project TEXT REFERENCES project NOT NULL, 
    id TEXT NOT NULL, 
    name TEXT, 
    description TEXT, 
    PRIMARY KEY ( project, id ) );

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
    RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER create_granting BEFORE INSERT ON granting FOR EACH ROW EXECUTE PROCEDURE create_granting();

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
