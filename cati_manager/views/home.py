from __future__ import absolute_import

from pyramid.view import view_config
from pyramid.security import Authenticated


@view_config(route_name='home', renderer='templates/home_anonymous.jinja2')
def home_anonymous(request):
    return {'title': 'CATI Manager', 'settings': request.authenticated_userid}


@view_config(route_name='home', renderer='templates/home_authenticated.jinja2',
             effective_principals=Authenticated)
def home_authenticated(request):
    return {'title': 'CATI Manager', 'settings': request.authenticated_userid}
