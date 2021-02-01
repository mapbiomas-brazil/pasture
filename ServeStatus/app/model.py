from flask_mongoengine import MongoEngine

db = MongoEngine()


def configure(app):
    db.init_app(app)
    app.db = db


class Task(db.Document):
    id_ = db.StringField()
    task_id = db.StringField()
    version = db.StringField()
    state = db.StringField()
    name = db.StringField()
    num = db.IntField()

    # version,name,task.state,task.id

class Config(db.Document):
    id_ = db.StringField()
    list_task = db.ListField(db.StringField(max_length=50))
    version = db.StringField()
    QUANTITY_ALLOWED_IN_QUEUE = db.IntField()