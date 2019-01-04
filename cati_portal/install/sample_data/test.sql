-- cati_portal changeset : sample_data
INSERT INTO cati_portal.identity (login, password, email, first_name, last_name) 
    VALUES ('just_registered', 'just_registered', 'just_registered@cati-neuroimaging.com', 'Just', 'Registered');
INSERT INTO cati_portal.identity (login, password, email, first_name, last_name) 
    VALUES ('just_registered2', 'just_registered2', 'just_registered2@cati-neuroimaging.com', 'Just', 'Registered2');

INSERT INTO cati_portal.identity (login, password, email, email_verification_time, first_name, last_name) 
    VALUES ('email_verified', 'email_verified', 'email_verified@cati-neuroimaging.com', now(), 'Email', 'Verified');
INSERT INTO cati_portal.identity (login, password, email, email_verification_time, first_name, last_name) 
    VALUES ('email_verified2', 'email_verified2', 'email_verified2@cati-neuroimaging.com', now(), 'Email', 'Verified2');

INSERT INTO cati_portal.identity (login, password, email, email_verification_time, first_name, last_name) 
    VALUES ('valid', 'valid', 'valid_user@cati-neuroimaging.com', now(), 'Valid', 'User');
INSERT INTO cati_portal.granting (project, credential, login) VALUES ('cati_portal', 'valid_user', 'valid');


INSERT INTO cati_portal.identity (login, password, email, email_verification_time, first_name, last_name) 
    VALUES ('usermod', 'usermod', 'user_moderator@cati-neuroimaging.com', now(), 'User', 'Moderator');
INSERT INTO cati_portal.granting (project, credential, login) VALUES ('cati_portal', 'valid_user', 'usermod');
INSERT INTO cati_portal.granting (project, credential, login) VALUES ('cati_portal', 'user_moderator', 'usermod');

INSERT INTO cati_portal.identity (login, password, email, email_verification_time, first_name, last_name) 
    VALUES ('admin', 'admin', 'admin@cati-neuroimaging.com', now(), 'Your', 'Master');
INSERT INTO cati_portal.granting (project, credential, login) VALUES ('cati_portal', 'valid_user', 'admin');
INSERT INTO cati_portal.granting (project, credential, login) VALUES ('cati_portal', 'server_admin', 'admin');
INSERT INTO cati_portal.granting (project, credential, login) VALUES ('cati_portal', 'user_moderator', 'admin');
