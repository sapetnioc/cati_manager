'''This is the WSGI entry point for cati_portal
'''

from functools import partial
import logging.config
import os
import os.path as osp

from flask import Flask
from flask_login import LoginManager

from cati_portal.http.authentication import User
from cati_portal.rest import RestAPI

def create_app(test_config=None):

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
    app = Flask(__name__, instance_path='/cati_portal/flask_instance', instance_relative_config=True)
    secret_key_file = osp.join(os.environ.get('CATI_PORTAL_DIR', '/cati_portal'), 'pgp', 'secret.key')
    app.secret_key = open(secret_key_file, 'rb').read()

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_json('config.json')
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    login_manager = LoginManager(app)
    login_manager.login_view = 'authentication.login'

    login_manager.user_loader(partial(User.get, bypass_access_rights=True))

    app.jinja_env.add_extension('jinja2.ext.do')

    api = RestAPI(app,
        title='CATI portal API',
        description='The REST API for CATI portal',
        version='0.0.1',
    )

    from . import db
    db.init_app(app)

    from .rest import init_api
    init_api(api)
    
    from .rest.authentication import init_api
    init_api(api)

    from .rest.database import init_api
    init_api(api)
    
    #from .http import authentication
    #app.register_blueprint(authentication.bp)

    #from .http import home
    #app.register_blueprint(home.bp)

    #from .http import settings
    #app.register_blueprint(settings.bp)

    return app

application = create_app()


if __name__ == '__main__':
    application.run()
