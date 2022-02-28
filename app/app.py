from flask import Flask

from .bulletin.UserView import UserView
from .bulletin.BoardView import BoardView
from .bulletin.PostView import PostView
from .bulletin.ThreadView import ThreadView

from .bulletin.model.Model import ModelUser

from flask_jwt_extended import JWTManager


class AppContext(object):
    _app = None

    def __init__(self):
        raise Exception("Instantiating not allowed")

    @classmethod
    def app(cls):
        if cls._app is None:
            cls._app = Flask(__name__)
            UserView.register(cls._app, trailing_slash=False)
            BoardView.register(cls._app, trailing_slash=False)
            PostView.register(cls._app, trailing_slash=False)
            ThreadView.register(cls._app, trailing_slash=False)
        return cls._app


app = AppContext.app()

app.config["JWT_SECRET_KEY"] = "BD1D66C8AC839DB679BBE10645DE1FA92F8524471C6DE8D1FAC9AF401EE388A3"  # TODO: Dynamically retrieve this if staging or production
jwt = JWTManager(app)


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.user_id


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    print(identity)
    return ModelUser.query.filter_by(user_id=identity).one_or_none()