import base64
try:
    from secret import choice
except:
    from random import choice
    import datetime 
import hashlib
import json
import os
import os.path as osp
import string

import pgpy
from flask import current_app, g
from flask_login import UserMixin



password_characters = string.ascii_letters + string.digits
def generate_password(size):
    return ''.join(choice(password_characters) for i in range(size))


def pgp_secret_key():
    default_key_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'pgp', 'secret.key')
    if current_app:
        secret_key_file = current_app.config.get('PGP_SECRET_KEY', default_key_file)
    else:
        secret_key_file = default_key_file
    if osp.exists(secret_key_file):
        pgp_secret_key, other = pgpy.PGPKey.from_file(secret_key_file)
        return pgp_secret_key
    raise FileNotFoundError('Cannot find pgp secret key file')


def pgp_public_key():
    default_key_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'pgp', 'public.key')
    if current_app:
        public_key_file = current_app.config.get('PGP_PUBLIC_KEY', default_key_file)
    else:
        public_key_file = default_key_file
    if osp.exists(public_key_file):
        pgp_public_key, other = pgpy.PGPKey.from_file(public_key_file)
        return pgp_public_key
    raise FileNotFoundError('Cannot find pgp public key file')


def hash_password(password):
    public_key = pgp_public_key()
    salted = pgpy.PGPMessage.new((password + generate_password(22)).encode('UTF8'), sensitive=True, format='b')
    return bytes(public_key.encrypt(salted))


def check_password(password, hash):
    secret_key = pgp_secret_key()
    # Salt length is 22 bytes
    pwd = secret_key.decrypt(pgpy.PGPMessage.from_blob(hash)).message[:-22].decode('UTF8')
    return password == pwd

from cati_portal.db import _get_admin_cursor

class User:
    def __init__(self, login):
        with _get_admin_cursor() as cur:
            sql = 'SELECT email, first_name, last_name, institution, email_verification_time, deactivation_time FROM cati_portal.identity WHERE login = %s'
            cur.execute(sql, [login])
            if cur.rowcount:
                self.login = login
                self.email, self.first_name, self.last_name, self.institution, activation_time, deactivation_time = cur.fetchone()
                self.is_authenticated = True
                self.is_active = (activation_time is not None and deactivation_time is None)
                self.is_anonymous = False
                return
        self.login = None
        self.email = self.first_name = self.last_name = self.institution = None
        self.is_authenticated = False
        self.is_active = False
        self.is_anonymous = True
    
    @staticmethod
    def new(login, password, email, first_name=None, last_name=None, institution=None):
        '''
        Create a new user in the database
        '''
        with _get_admin_cursor() as cur:
            sql = 'INSERT INTO cati_portal.identity(login, password, email, first_name, last_name, institution) VALUES (%s, %s, %s, %s, %s, %s)'
            cur.execute(sql, [login, password, email, first_name, last_name, institution])
        return User(login)
    
    def get_id(self):
        return self.login
    
    def check_password(self, password_to_check):
        '''
        Check the password of a user
        '''
        if self.login:
            with _get_admin_cursor() as cur:
                sql = 'SELECT password FROM cati_portal.identity WHERE login = %s'
                cur.execute(sql, [self.login])
                if cur.rowcount == 1:
                    encrypted = cur.fetchone()[0].tobytes()
                    pwd = pgp_secret_key().decrypt(pgpy.PGPMessage.from_blob(encrypted)).message[:-22].decode('UTF8') # Salt length is 22 bytes
                    return pwd == password_to_check
        return False
    
    def validate_email(self, time=None):
        '''
        Set email verification time for the current user. If no time is given, datetime.now() is used 
        '''
        if time is None:
            time = datetime.datetime.now()
        with _get_admin_cursor() as cur:
            sql = 'UPDATE cati_portal.identity SET email_verification_time = %s WHERE login = %s'
            cur.execute(sql, [time, self.login])


    def check_credential(self, required):
        if self.is_active:
            l = required.split('.', 1)
            if len(l) != 2:
                raise ValueError(f'Invalid credential string "{required}". It must have the form "<project>.<credential>".')
            project, credential = l
            with _get_admin_cursor() as cur:
                sql = 'SELECT COUNT(*) FROM cati_portal.granting WHERE project = %s AND credential = %s AND login = %s'
                cur.execute(sql, [project, credential, self.login])
                return (cur.fetchone()[0] == 1)
        return False
