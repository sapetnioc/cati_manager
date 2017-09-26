from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

def authentication_callback(login, request):
    '''
    ldap_authentication_callback can be used as callback for
    AuthTktAuthenticationPolicy. It checks user password and 
    returns either None if the user is not authenticated or a
    list composed of the user login and the groups it
    belongs to (each group name is added a prefix 'group:').
    '''
    return [ login ]

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    authn_policy = AuthTktAuthenticationPolicy('jfldezkjvmezafkjsdqmlfkjd', 
        hashalg='sha512',
        timeout=1200,      # User must reidentify himself after 20 minutes
        reissue_time=120,  # Authentication coockie is recreated every 2 min
        callback=authentication_callback)
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.scan()
    return config.make_wsgi_app()
