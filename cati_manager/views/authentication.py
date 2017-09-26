from __future__ import absolute_import

import urllib

from pyramid.view import view_config, forbidden_view_config
from pyramid.security import remember, forget
from pyramid.httpexceptions import HTTPFound



@forbidden_view_config(renderer='templates/login.jinja2')
def forbidden(context, request):
    if not request.authenticated_userid:
        url = '/login?%s' % urllib.urlencode({'came_from': request.url})
        subrequest = request.blank(url, cookies=request.cookies)
        subrequest.registry = request.registry
        response = request.invoke_subrequest(subrequest)
        return response
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
        if True: # TODO: check password here
            headers = remember(request, login)
            return HTTPFound(location=came_from,
                             headers=headers)
        else:
            message = 'Invalid user name or password'

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
