from ServeStatus.app.controller.config import bp_config
from ServeStatus.app.controller.task import bp_task


def init_app(app):
    app.register_blueprint(bp_config)
    app.register_blueprint(bp_task)