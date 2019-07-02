import datetime
from typing import Optional, NoReturn

def init_api(api):
    @api.schema
    class NewIdentity:
        login: str
        password: bytes
        email: str
        first_name: Optional[str]
        last_name: Optional[str]
        institution: Optional[str]

    @api.schema
    class Identity(NewIdentity):
        registration_time: Optional[datetime.datetime]
        email_verification_time: Optional[datetime.datetime]
        activation_time: Optional[datetime.datetime]
        deactivation_time: Optional[datetime.datetime]


    @api.path('/install')
    def post(installation_hash : str, admin : NewIdentity) -> NoReturn:
        '''Perform server installation'''
        hash_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'tmp', 'installation.hash')
        if osp.exists(hash_file):
            hash = open(hash_file, 'rb').read()
            if check_password(form.install_code.data, hash):
                user = User.create(login=admin.login,
                                    email=admin.email,
                                    password=admin.password,
                                    first_name=admin.first_name,
                                    last_name=admin.last_name,
                                    institution=admin.institution)
                with _get_admin_cursor() as cur:
                    time = datetime.datetime.now()
                    sql = 'UPDATE cati_portal.identity SET activation_time = %s, email=%s, email_verification_time = %s WHERE login = %s;'
                    cur.execute(sql, [time, user.email, time, user.login])
                    sql = 'INSERT INTO cati_portal.granting (login, project, credential) VALUES (%s, %s, %s);'
                    cur.executemany(sql, [[user.login, 'cati_portal', 'server_admin'],
                                            [user.login, 'cati_portal', 'user_moderator']])
                    flash(f'Administrator {form.login.data} succesfully registered and activated with server and user management rights', 'success')
                    user = User.get(user.login, bypass_access_rights=True)
                    login_user(user)
                    os.remove(hash_file)
            abort(403)
        abort(404)
