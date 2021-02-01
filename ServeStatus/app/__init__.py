from flask import Flask
from dynaconf import settings
from .model import configure as config_db



def create_app():
    app = Flask(__name__)

    app.config['MONGODB_SETTINGS'] = {
    'db': settings.DB,
    'host': settings.DB_HOST,
    'port': settings.DB_PORT
        }

    config_db(app)


    from .task import bp_task
    app.register_blueprint(bp_task, url_prefix='/task')

    from .config import bp_config
    app.register_blueprint(bp_config)


    return app