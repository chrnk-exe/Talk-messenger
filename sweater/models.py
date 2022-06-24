from datetime import datetime

from flask_login import UserMixin

from sweater import db, login_manager


class User(db.Model, UserMixin):
    # __bind_key__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(40), nullable=False)
    password = db.Column(db.Text, nullable=False)
    is_activated = db.Column(db.Boolean, default=False)
    dialogs = db.Column(db.Text, default="[]")
    unread_dialogs = db.Column(db.Text, default="{}")
    date_create = db.Column(db.String(30))
    date_visited = db.Column(db.String(30))
    user_status = db.Column(db.Integer, default=0)
    avatar_id = db.Column(db.Integer)

    def is_active(self):
        return self.is_activated


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class Dialog(db.Model):
    # __bind_key__ = 'dialogs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), nullable=True)
    members = db.Column(db.Text)
    talks = db.Column(db.Text, default="[]")
    date_create = db.Column(db.String(30))
    date_update = db.Column(db.String(30), onupdate=str(datetime.utcnow()))


class Talk(db.Model):
    # __bind_key__ = 'talks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40), nullable=False)
    messages = db.Column(db.Text, default="[]")
    date_create = db.Column(db.String(30))
    date_update = db.Column(db.String(30), onupdate=str(datetime.utcnow()))


class Message(db.Model):
    # __bind_key__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    value = db.Column(db.Text, nullable=False)
    date_create = db.Column(db.String(30))


class Media(db.Model):
    # __bind_key__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    date_create = db.Column(db.String(30))
