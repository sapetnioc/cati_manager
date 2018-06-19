from __future__ import absolute_import

from pyramid.view import view_config

from cati_portal.postgres import user_connect
from cati_portal.views.admin import check_maintenance

def includeme(config):
    config.add_route('user', '/user/{login}')

@view_config(route_name='user', request_method='DELETE', renderer='templates/layout.jinja2',
             permission='cati_portal_user_moderator')
def delete_user(request):
    check_maintenance(request)
    login = request.matchdict['login']
    with user_connect(request) as db:
        with db.cursor() as cur:
            sql = 'DELETE FROM cati_portal.identity WHERE login=%s'
            cur.execute(sql, [login])
    return {'title': 'Succesful deletion',
            'content': 'User %s had been succesfully deleted'}

@view_config(route_name='user', request_method='PUT', renderer='templates/layout.jinja2',
             permission='cati_portal_user_moderator')
def validate_user(request):
    check_maintenance(request)
    login = request.matchdict['login']
    with user_connect(request) as db:
        with db.cursor() as cur:
            sql = 'SELECT COUNT(*) FROM cati_portal.identity_email_not_verified WHERE login = %s'
            cur.execute(sql, [login])
            if cur.fetchone()[0]:
                sql = 'UPDATE cati_portal.identity SET email_verification_time = now() WHERE login = %s;'
                cur.execute(sql, [login])
            sql = "INSERT INTO cati_portal.granting (project, credential, login) VALUES ('cati_portal', 'valid_user', %s);"
            cur.execute(sql, [login])
    return {'title': 'Succesfull validation',
            'content': 'User %s had been succesfully validated'}
