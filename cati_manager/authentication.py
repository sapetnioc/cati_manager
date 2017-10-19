import os.path as osp
import hashlib
import base64
import json

from cati_manager.postgres import manager_connect


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
            challenge = base64.b64decode(challenge)
            return hashlib.sha256(password.encode('utf-8')+challenge[32:]).digest() == challenge[:32]
    else:
        with manager_connect(request) as db:
            with db.cursor() as cur:
                cur.execute('SELECT password FROM cati_manager.identity WHERE login=%s', [login])
                if cur.rowcount:
                    challenge = cur.fetchone()[0].tobytes()
                    return hashlib.sha256(password.encode('utf-8')+challenge[32:]).digest() == challenge[:32]
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
