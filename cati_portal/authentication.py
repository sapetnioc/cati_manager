import base64
try:
    from secret import choice
except:
    from random import choice
import hashlib
import json
import os
import os.path as osp
import string

import pgpy
from flask import current_app, g

from cati_portal.postgres import manager_connect


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
    salted = pgpy.PGPMessage.new(password + generate_password(22), sensitive=True)
    return bytes(public_key.encrypt(salted))


def check_password(password, hash):
    secret_key = pgp_secret_key()
    # Salt length is 22 bytes
    pwd = secret_key.decrypt(pgpy.PGPMessage.from_blob(hash)).message[:-22] 
    return password == pwd


if __name__ == '__main__':
    # Create an installation password and store its hash representation
    hash_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'tmp', 'installation.hash')
    installation_password = generate_password(16)
    open(hash_file, 'wb').write(hash_password(installation_password))
    print(installation_password, end='')

#def get_user_password(request, login=None):
    #if login is None:
        #login = request.authenticated_userid
    #key = get_pgp_secret_key(request)
    #with manager_connect(request) as db:
        #with db.cursor() as cur:
            #cur.execute('SELECT password FROM cati_portal.identity WHERE login=%s', [login])
            #if cur.rowcount:
                #encrypted = cur.fetchone()[0].tobytes()
                #pwd = key.decrypt(pgpy.PGPMessage.from_blob(encrypted)).message[:-22] # Salt length is 22 bytes
                #return pwd.decode('UTF8')
    #return None


#def check_password(login, password, request):
    #admin_login = request.registry.settings['cati_portal.database_admin']
    #if login == admin_login:
        #admin_challenge = request.registry.settings['cati_portal.database_admin_challenge']
        #return hashlib.sha256(password.encode('utf-8')).hexdigest() == admin_challenge
    #maintenance_path = osp.expanduser(request.registry.settings['cati_portal.maintenance_path'])
    #if osp.exists(maintenance_path):
        #maintenance = json.load(open(maintenance_path))
        #challenge = maintenance['admins'].get(login)
        #if challenge:
            #key = get_pgp_secret_key(request)
            #encrypted = base64.b64decode(challenge)
            ## Salt length is 22 bytes
            #pwd = key.decrypt(pgpy.PGPMessage.from_blob(encrypted)).message[:-22].decode('UTF8') 
            #return password == pwd
    #else:
        #return password == get_user_password(request, login)
    #return False


#def authentication_callback(login, request):
    #'''
    #authentication_callback can be used as callback for
    #AuthTktAuthenticationPolicy. It returns a
    #list composed of the user login and the credentials it
    #had been granted.
    #'''
    #maintenance_path = osp.expanduser(request.registry.settings['cati_portal.maintenance_path'])
    #if osp.exists(maintenance_path):
        #maintenance = json.load(open(maintenance_path))
        #if login in maintenance['admins']:
            #return [ login, 'cati_portal_server_admin' ]
    #else:
        #with manager_connect(request) as db:
            #with db.cursor() as cur:
                #sql = ('SELECT DISTINCT c.project, c.id '
                       #'FROM cati_portal.identity i, cati_portal.granting g, project p, credential c '
                       #'WHERE i.login=%s AND g.login = i.login AND c.id = g.credential;')
                #cur.execute(sql, [login])
                #principals = ['%s_%s' % i for i in cur]
                #if not principals:
                    ## Check that the user exists
                    #cur.execute('SELECT count(*) FROM cati_portal.identity WHERE login = %s;', [login])
                    #if not cur.fetchone():
                        #return None
        #return [ login ] + principals
    #return None
