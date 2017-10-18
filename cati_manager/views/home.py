from __future__ import absolute_import

from pyramid.view import view_config
from pyramid.security import Authenticated
from pyramid.httpexceptions import HTTPFound

from cati_manager.views.admin import check_maintenance

@view_config(route_name='home', renderer='templates/home.jinja2')
def home_anonymous(request):
    check_maintenance(request)
    return {}


@view_config(route_name='home', renderer='templates/home.jinja2',
             effective_principals=Authenticated)
def home_authenticated(request):
    check_maintenance(request)
    if request.has_permission('cati_manager_valid_user'):
        return HTTPFound('/dashboard')
    else:
        return {'title': 'CATI Manager'}
