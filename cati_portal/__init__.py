from functools import partial
import logging.config
import os
import os.path as osp

def create_app(test_config=None):
    # Some submodules are used in an environement without thirdparty module installed.
    # Therefore flask cannot be used at module level.
    from flask import Flask
    from flask_login import LoginManager
    
    from cati_portal.authentication import User
    
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

    from . import db
    db.init_app(app)
    
    from . import authentication
    app.register_blueprint(authentication.bp)

    from . import home
    app.register_blueprint(home.bp)

    from . import settings
    app.register_blueprint(settings.bp)

    return app
