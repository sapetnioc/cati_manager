import logging.config


def create_app(test_config=None):
    # Some submodules are used in an environement without thirdparty module installed.
    # Therefore flask cannot be used at module level.
    from flask import Flask
    
    logging.config.dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'wsgi': {
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'default',
            'filename': '/cati_portal/log/cati_portal.log',
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['wsgi']
        }
    })
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py')
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    from . import db
    db.init_app(app)
    
    # a simple page that says hello
    @app.route('/hello')
    def hello():
        with db.get_cursor() as cur:
            cur.execute('SELECT * FROM cati_portal.identity;')
            return str(cur.fetchall())
        return 'Hello, World!'

    return app

#import datetime
#import warnings

#from pyramid.config import Configurator
#from pyramid.authentication import AuthTktAuthenticationPolicy
#from pyramid.authorization import ACLAuthorizationPolicy
#from pyramid.session import UnencryptedCookieSessionFactoryConfig
#from pyramid.renderers import JSON

#from cati_portal.authentication import authentication_callback

#class PrincipalAuthorizationPolicy:
    #def permits(self, context, principals, permission):
        #""" Return ``True`` if any of the ``principals`` is allowed the
        #``permission`` in the current ``context``, else return ``False``
        #"""
        #return permission in principals
    
    #def principals_allowed_by_permission(self, context, permission):
        #""" Return a set of principal identifiers allowed by the
        #``permission`` in ``context``.  This behavior is optional; if you
        #choose to not implement it you should define this method as
        #something which raises a ``NotImplementedError``.  This method
        #will only be called when the
        #``pyramid.security.principals_allowed_by_permission`` API is
        #used."""
        #return {permission}


#def main(global_config, **settings):
    #""" This function returns a Pyramid WSGI application.
    #"""
    #config = Configurator(settings=settings)
    #config.include('pyramid_jinja2')

    ## Make datetime.datetime objects useable in view returning
    ## JSON data. They are automatically converted to an ISO formatted
    ## string.
    #json_renderer = JSON()
    #def datetime_adapter(obj, request):
        #return obj.isoformat()
    #json_renderer.add_adapter(datetime.datetime, datetime_adapter)
    #config.add_renderer('json2', json_renderer)

    #authn_policy = AuthTktAuthenticationPolicy('jfldezkjvmezafkjsdqmlfkjd', 
        #hashalg='sha512',
        #timeout=1200,      # User must reidentify himself after 20 minutes
        #reissue_time=120,  # Authentication coockie is recreated every 2 min
        #callback=authentication_callback)
    #authz_policy = PrincipalAuthorizationPolicy()
    #session_factory = UnencryptedCookieSessionFactoryConfig('ẑposfvevzê4')
    #config.set_authorization_policy(authz_policy)
    #config.set_authentication_policy(authn_policy)
    #config.set_session_factory(session_factory)
    #config.add_static_view('static', 'static', cache_max_age=3600)
    #config.add_route('home', '/')
    #config.include('.views.authentication')
    #config.include('.views.database')
    #config.include('.views.user')
    #config.include('.views.dashboard')
    #config.include('.views.admin')
    #config.include('.views.upload')
    #config.include('.views.project')
    #config.add_route('test', '/test')
    #config.scan('cati_portal.views')
        
    ## pgpy emit warnings that can be ignored
    ## I do not know how to select warnings to ignore.
    #warnings.filterwarnings('ignore')
    
    #return config.make_wsgi_app()