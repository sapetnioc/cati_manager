from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import UnencryptedCookieSessionFactoryConfig

import deform

from cati_manager.postgres import authentication_callback

class PrincipalAuthorizationPolicy:
    def permits(self, context, principals, permission):
        """ Return ``True`` if any of the ``principals`` is allowed the
        ``permission`` in the current ``context``, else return ``False``
        """
        return permission in principals
    
    def principals_allowed_by_permission(self, context, permission):
        """ Return a set of principal identifiers allowed by the
        ``permission`` in ``context``.  This behavior is optional; if you
        choose to not implement it you should define this method as
        something which raises a ``NotImplementedError``.  This method
        will only be called when the
        ``pyramid.security.principals_allowed_by_permission`` API is
        used."""
        return {permission}


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
    authz_policy = PrincipalAuthorizationPolicy()
    session_factory = UnencryptedCookieSessionFactoryConfig('ẑposfvevzê4')
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.set_session_factory(session_factory)
    
    deform.renderer.configure_zpt_renderer()
    config.add_static_view('static_deform', 'deform:static')
    
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('table_info', '/db/table/{table}/info')
    config.add_route('table_data', '/db/table/{table}/data')
    config.add_route('query_info', '/db/query/{query}/info')
    config.add_route('query_data', '/db/query/{query}/data')
    config.add_route('test', '/test')
    config.scan()
    return config.make_wsgi_app()
