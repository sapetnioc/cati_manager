from __future__ import absolute_import

import html
import hashlib

import psycopg2

from pyramid.view import view_config, forbidden_view_config
from pyramid.security import remember, forget
from pyramid.httpexceptions import HTTPFound

from cati_manager.postgres import manager_connect, table_info, table_insert

def includeme(config):
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('register', '/register')


@forbidden_view_config(renderer='templates/login.jinja2')
def forbidden(context, request):
    if not request.authenticated_userid:
        url = '%s?came_from=%s' % (request.route_url('login'), html.escape(request.url))
        request.session.flash('You must be logged in to access the requested page', 'warning')
        return HTTPFound(location=url)
    else:
        return context


@view_config(route_name='login', renderer='templates/login.jinja2')
def login(request):
    login_url = request.route_url('login')
    referrer = request.url
     # Don't use login form itself as came_from (we redirect to application url)
    if referrer == login_url:
        referrer = request.application_url
    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''
    if 'form.submitted' in request.params:
        login = request.params['login']
        password = request.params['password']
        with manager_connect(request) as db:
            with db.cursor() as cur:
                cur.execute('SELECT password FROM cati_manager.identity WHERE login=%s', [login])
                if cur.rowcount:
                    challenge = cur.fetchone()[0].tobytes()
                    if hashlib.sha256(password.encode('utf-8')+challenge[32:]).digest() == challenge[:32]:
                        headers = remember(request, login)
                        return HTTPFound(location=came_from,
                                         headers=headers)
        message = 'Invalid user name or password'
        #database_url = request.registry.settings['cati_manager.database']
        #try:
            #psycopg2.connect(database_url, user=login, password=password)
            #headers = remember(request, login)
            #return HTTPFound(location=came_from,
                             #headers=headers)
        #except psycopg2.Error:
            #message = 'Invalid user name or password'

    return dict(
        message=message,
        url=request.application_url + '/login',
        came_from=came_from)


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    url = request.route_url('home')
    return HTTPFound(location=url,
                     headers=headers)


@view_config(route_name='register', request_method='GET', renderer='templates/database_form.jinja2')
def registration_form(request):
    return {
        'data_type': 'registration',
        'db_info': table_info(manager_connect(request), 'cati_manager', 'identity'),
        'button': 'register',
    }

@view_config(route_name='register', request_method='POST', renderer='json')
def registration_validation(request):
    errors = {}
    login = request.params['login']
    with manager_connect(request) as db:
        with db.cursor() as cur:
            sql = 'SELECT count(*) FROM cati_manager.identity WHERE login = %s'
            cur.execute(sql, [login])
            if cur.fetchone()[0]:
                errors['login'] = 'You must choose another login'
            if not request.params['password']:
                errors['password'] = 'Password is mandatory'
            if request.params['password'] != request.params['check_password']:
                errors['check_password'] = 'Differs from password'
            if errors:
                return errors
            data = dict(request.params)
            del data['check_password']
            table_insert(db, 'cati_manager', 'identity', data=[data])
    request.session.flash('User %s sucessfuly registered' % login, 'success')
    return {'redirection': request.application_url}
