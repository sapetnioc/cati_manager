import os.path as osp
import hashlib
import base64
import json

import pgpy

from cati_manager.postgres import manager_connect

pgp_secret_key = None
def get_pgp_secret_key(request):
    global pgp_secret_key
    if pgp_secret_key is None:
        path= osp.expandvars(request.registry.settings['cati_manager.pgp_secret_key'])
        pgp_secret_key, other = pgpy.PGPKey.from_file(path)
    return pgp_secret_key


def get_user_password(request, login=None):
    if login is None:
        login = request.authenticated_userid
    key = get_pgp_secret_key(request)
    with manager_connect(request) as db:
        with db.cursor() as cur:
            cur.execute('SELECT password FROM cati_manager.identity WHERE login=%s', [login])
            if cur.rowcount:
                encrypted = cur.fetchone()[0].tobytes()
                pwd = key.decrypt(pgpy.PGPMessage.from_blob(encrypted)).message[:-22] # Salt length is 22 bytes
                return pwd.decode('UTF8')
    return None


def check_password(login, password, request):
    admin_login = request.registry.settings['cati_manager.database_admin']
    if login == admin_login:
        admin_challenge = request.registry.settings['cati_manager.database_admin_challenge']
        return hashlib.sha256(password.encode('utf-8')).hexdigest() == admin_challenge
    maintenance_path = osp.expanduser(request.registry.settings['cati_manager.maintenance_path'])
    if osp.exists(maintenance_path):
        maintenance = json.load(open(maintenance_path))
        challenge = maintenance['admins'].get(login)
        if challenge:
            key = get_pgp_secret_key(request)
            encrypted = base64.b64decode(challenge)
            # Salt length is 22 bytes
            pwd = key.decrypt(pgpy.PGPMessage.from_blob(encrypted)).message[:-22].decode('UTF8') 
            return password == pwd
    else:
        return password == get_user_password(request, login)
    return False


def authentication_callback(login, request):
    '''
    authentication_callback can be used as callback for
    AuthTktAuthenticationPolicy. It returns a
    list composed of the user login and the credentials it
    had been granted.
    '''
    maintenance_path = osp.expanduser(request.registry.settings['cati_manager.maintenance_path'])
    if osp.exists(maintenance_path):
        maintenance = json.load(open(maintenance_path))
        if login in maintenance['admins']:
            return [ login, 'cati_manager_server_admin' ]
    else:
        with manager_connect(request) as db:
            with db.cursor() as cur:
                sql = ('SELECT DISTINCT c.project, c.id '
                       'FROM cati_manager.identity i, cati_manager.granting g, project p, credential c '
                       'WHERE i.login=%s AND g.login = i.login AND c.id = g.credential;')
                cur.execute(sql, [login])
                principals = ['%s_%s' % i for i in cur]
                if not principals:
                    # Check that the user exists
                    cur.execute('SELECT count(*) FROM cati_manager.identity WHERE login = %s;', [login])
                    if not cur.fetchone():
                        return None
        return [ login ] + principals
    return None
