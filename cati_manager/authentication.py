import hashlib
from cati_manager.postgres import manager_connect

def check_password(login, password, request):
    admin_login = request.registry.settings['cati_manager.database_admin']
    if login == admin_login:
        admin_challenge = request.registry.settings['cati_manager.database_admin_challenge']
        return hashlib.sha256(password.encode('utf-8')).hexdigest() == admin_challenge
    with manager_connect(request) as db:
        with db.cursor() as cur:
            cur.execute('SELECT password FROM cati_manager.identity WHERE login=%s', [login])
            if cur.rowcount:
                challenge = cur.fetchone()[0].tobytes()
                return hashlib.sha256(password.encode('utf-8')+challenge[32:]).digest() == challenge[:32]
    return False
