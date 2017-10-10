from __future__ import absolute_import

from pyramid.view import view_config

from cati_manager.postgres import user_connect

def includeme(config):
    config.add_route('user', '/user/{login}')

@view_config(route_name='user', request_method='DELETE', renderer='templates/layout.jinja2',
             permission='cati_manager_user_moderator')
def delete_user(request):
    login = request.matchdict['login']
    with user_connect(request) as db:
        with db.cursor() as cur:
            sql = 'DELETE FROM cati_manager.identity WHERE login=%s'
            cur.execute(sql, [login])
    return {'title': 'Succesful deletion',
            'content': 'User %s had been succesfully deleted'}

@view_config(route_name='user', request_method='PUT', renderer='templates/layout.jinja2',
             permission='cati_manager_user_moderator')
def validate_user(request):
    login = request.matchdict['login']
    with user_connect(request) as db:
        with db.cursor() as cur:
            sql = 'SELECT COUNT(*) FROM cati_manager.identity_email_not_verified WHERE login = %s'
            cur.execute(sql, [login])
            if cur.fetchone()[0]:
                sql = 'UPDATE cati_manager.identity SET email_verification_time = now() WHERE login = %s;'
                cur.execute(sql, [login])
            sql = "INSERT INTO cati_manager.granting (project, credential, login) VALUES ('cati_manager', 'valid_user', %s);"
            cur.execute(sql, [login])
    return {'title': 'Succesfull validation',
            'content': 'User %s had been succesfully validated'}