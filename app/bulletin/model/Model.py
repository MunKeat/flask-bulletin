import enum

from datetime import datetime
from passlib.hash import sha256_crypt
from sqlalchemy import BigInteger, Column, ColumnDefault, DateTime, Enum, ForeignKey, Unicode, UnicodeText
from sqlalchemy.orm import declarative_base, relationship, scoped_session, sessionmaker

from ...common.database_conn import get_engine

Session = scoped_session(sessionmaker())
session = Session.configure(bind=get_engine())

Base = declarative_base()


# TODO Split into multiple smaller files for readability
# Currently errors at: error retrieving data; unable to get board_id=7; err=When initializing mapper mapped class ModelPost->posts, expression 'ModelThread' failed to locate a name ('ModelThread'). If this is a class name, consider adding this relationship() to the <class 'flask-bulletin.app.bulletin.model.ModelBoard.ModelPost'> class after both dependent classes have been defined.


class ModelThread(Base):
    __tablename__ = "threads"
    query = Session.query_property()
    thread_id = Column(BigInteger, primary_key=True)
    post_id = Column(BigInteger, ForeignKey("posts.post_id"))
    thread_owner = Column(BigInteger, ForeignKey("users.user_id"))
    thread_content = Column(UnicodeText)
    date_created = Column(DateTime, ColumnDefault(datetime.now()))

    def repr(self):
        representation = {
            "post_id": self.post_id,
            "thread_id": self.thread_id,
            "thread_content": self.thread_content,
            "date_created": self.date_created,
        }
        return representation


class ModelPost(Base):
    __tablename__ = "posts"
    query = Session.query_property()
    board_id = Column(BigInteger, ForeignKey("boards.board_id"))
    post_id = Column(BigInteger, primary_key=True)
    post_owner = Column(BigInteger, ForeignKey("users.user_id"))
    post_title = Column(Unicode(256))
    date_created = Column(DateTime, ColumnDefault(datetime.now()))
    #
    post_threads = relationship("ModelThread")

    def repr(self):
        representation = {
            "post_id": self.post_id,
            "board_id": self.board_id,
            "post_title": self.post_title,
            "date_created": self.date_created,
        }
        return representation


class BoardModerationStatusEnum(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    PENDING = "PENDING"


class ModelBoardModerator(Base):
    __tablename__ = "boards_moderators"
    query = Session.query_property()
    board_moderator_id = Column(BigInteger, primary_key=True)
    board_id = Column(BigInteger, ForeignKey("boards.board_id"))
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    status = Column(Enum(BoardModerationStatusEnum))
    date_created = Column(DateTime, ColumnDefault(datetime.now()))

    def repr(self):
        representation = {
            "board_moderator_id": self.board_moderator_id,
            "board_id": self.board_id,
            "user_id": self.user_id,
            "status": self.status,
            "date_created": self.date_created,
        }
        return representation


class ModelBoard(Base):
    __tablename__ = "boards"
    query = Session.query_property()
    board_id = Column(BigInteger, primary_key=True)
    board_owner = Column(BigInteger, ForeignKey("users.user_id"))
    board_name = Column(Unicode(256))
    date_created = Column(DateTime, ColumnDefault(datetime.now()))
    #
    board_moderators = relationship(ModelBoardModerator.__name__)
    board_posts = relationship(ModelPost.__name__)

    def repr(self):
        representation = {
            "board_id": self.board_id,
            "board_name": self.board_name,
            "date_created": self.date_created,
        }
        return representation


class UserRoleEnum(str, enum.Enum):
    SUPERADMIN = "SUPERADMIN"
    STAFF = "STAFF"
    GUEST = "GUEST"


class ModelUser(Base):
    __tablename__ = "users"
    query = Session.query_property()
    user_id = Column(BigInteger, primary_key=True)
    email = Column(Unicode(320))
    username = Column(Unicode(64))
    salted_password = Column(Unicode(64))
    user_role = Column(Enum(UserRoleEnum))
    date_created = Column(DateTime, ColumnDefault(datetime.now()))
    #
    board_owners = relationship(ModelBoard.__name__)
    board_moderators = relationship(ModelBoardModerator.__name__)
    post_owner = relationship(ModelPost.__name__)

    def repr(self):
        representation = {
            "user_id": self.user_id,
            "email": self.email,
            "user_role": self.user_role,
            "date_created": self.date_created,
        }
        return representation

    def check_password(self, password):
        return sha256_crypt.verify(password, self.salted_password)


Base.metadata.create_all(get_engine())