from __future__ import absolute_import

import html
import hashlib
import datetime

import psycopg2

from pyramid.view import view_config, forbidden_view_config
from pyramid.security import remember, forget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from cati_manager.authentication import check_password
from cati_manager.postgres import manager_connect, table_info, table_insert

def includeme(config):
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('register', '/register')
    config.add_route('email_validation', '/register/{login}/{secret}')


@forbidden_view_config(renderer='templates/login.jinja2')
def forbidden(context, request):
    if not request.authenticated_userid:
        url = '%s?came_from=%s' % (request.route_url('login'), html.escape(request.url))
        request.session.flash('You must be logged in to access the requested page', 'warning')
        return HTTPFound(location=url)
    else:
        return context


@view_config(route_name='login', request_method='GET', renderer='templates/login.jinja2')
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
    return dict(
        message=message,
        url=request.application_url + '/login',
        came_from=came_from)


@view_config(route_name='login', request_method='POST', renderer='templates/login.jinja2')
def login_submission(request):
    login_url = request.route_url('login')
    referrer = request.url
     # Don't use login form itself as came_from (we redirect to application url)
    if referrer == login_url:
        referrer = request.application_url
    came_from = request.params.get('came_from', referrer)
    login = request.params['login']
    password = request.params['password']
    if check_password(login, password, request):
        headers = remember(request, login)
        return HTTPFound(location=came_from,
                          headers=headers)
    return dict(
        message='Invalid user name or password',
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
            if not request.params['email']:
                errors['email'] = 'Email is mandatory'
            if errors:
                return errors
            data = dict(request.params)
            del data['check_password']
            table_insert(db, 'cati_manager', 'identity', data=[data])
    request.session.flash('User %s sucessfuly registered' % login, 'success')
    return {'redirection': request.application_url}

@view_config(route_name='email_validation', request_method='GET', renderer='templates/layout.jinja2')
def email_validation(request):
    login = request.matchdict['login']
    secret = request.matchdict['secret']
    with manager_connect(request) as db:
        with db.cursor() as cur:
            cur.execute('SELECT count(*) '
                        'FROM cati_manager.identity_email_not_verified '
                        'WHERE login = %s AND '
                        '      secret = %s;', [login, secret])
            if cur.fetchone()[0]:
                cur.execute('UPDATE cati_manager.identity SET email_verification_time=%s WHERE login=%s',
                            [datetime.datetime.now().isoformat(), login])
                request.session.flash('Email verified for user %s. It is now necessary to wait for a moderator validation of the account in order to be able to use it.' % login, 'warning')
                return HTTPFound(location='/')
            raise HTTPNotFound()