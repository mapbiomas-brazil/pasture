from flask import Flask
from dynaconf import settings
from ServeStatus.app.model import configure as config_db
from ServeStatus.app import controller


def create_app():
    app = Flask(__name__)

    app.config['MONGODB_SETTINGS'] = {
    'db': settings.DB,
    'host': settings.DB_HOST,
    'port': settings.DB_PORT
        }

    config_db(app)
    controller.init_app(app)


    return app