from flask_classful import FlaskView, request, route
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..common.database_conn import get_engine
from .BoardView import get_board_by_id_or_name
from .model.Model import ModelPost, ModelBoard, ModelBoardModerator, ModelUser, UserRoleEnum


def get_post_by_id(post_id):
    try:
        if post_id:
            post_id = int(post_id)
            post = ModelPost.query.filter(ModelPost.post_id == post_id).one()
        else:
            raise Exception("need to provide post_id as input")
        return post
    except Exception as e:
        print(f"unable to retrieve post; error={e}")
        return None


def has_post_permission(user_id, board_id, post_id=None):
    user = ModelUser.query.filter(ModelUser.user_id == user_id).one()
    board = ModelBoard.query.filter(ModelBoard.board_id == board_id).one()
    is_superuser_or_staff = (user.user_role in [UserRoleEnum.SUPERADMIN, UserRoleEnum.STAFF])
    is_board_admin = (board.board_owner == user_id)
    if is_superuser_or_staff or is_board_admin:
        return True
    is_board_moderator = (ModelBoardModerator.query.filter(and_(ModelBoardModerator.board_id==board_id), (ModelBoardModerator.user_id==user_id)).count() == 1)
    if post_id is None:
        return is_board_moderator
    post = ModelPost.query.filter(ModelPost.post_id==post_id).one()
    is_post_owner = (post.post_owner == user_id)
    return is_post_owner


class PostView(FlaskView):
    @route("create", methods=["POST"])
    @jwt_required
    def create(self):
        """
        Create board with unique name
        """
        resp, status = {}, 500
        with Session(get_engine()) as session:
            try:
                board_id = request.form.get("board_id", None)
                board_name = request.form.get("board_name", None)
                post_title = request.form.get("post_title", None)
                board = get_board_by_id_or_name(board_id=board_id, board_name=board_name)
                if board is None:
                    return resp, status
                elif not post_title:
                    print(f"post_title={post_title} is not valid")
                    return resp, status
                # Check user permission
                user_id = get_jwt_identity()
                if not has_post_permission(user_id=user_id, board_id=board_id):
                    raise Exception("not allowed to modify board")
                post = ModelPost(post_owner=user_id , board_id=board_id, post_title=post_title)
                session.add(post)
                session.commit()
                session.refresh(post)
                resp["created"] = True
                resp.update(post.repr())
                session.commit()
                status = 201
            except Exception as e:
                session.rollback()
                # TODO Insert logging - for instance, a call to ElasticSearch to upload logs for easy debugging
                err_msg = f"unable to create post_title={post_title} in board={board_name}; err={e}"
                print(err_msg)
                resp = {
                    "created": False,
                    "board_id": board_id,
                    "post_id": None,
                    "datetime_created": None,
                    "error": err_msg,
                }
                status = 400
        return resp, status

    def get(self, post_id):
        """
        Get post,
        """
        resp, status = {}, 500
        try:
            post_id = int(post_id)
            post = ModelBoard.query.filter(ModelPost.post_id == post_id).one()
            if post is None:
                status = 404
            else:
                resp = post.repr()
                status = 200
        except ValueError as e:
            # TODO Insert logging - for instance, a call to centralised ElasticSearch to upload logs for easy debugging
            err_msg = f"expected post_id to be integer; unable to cast post_id={post_id}; err={e}"
            print(err_msg)
            resp["error"] = err_msg
        except Exception as e:
            # TODO Insert logging - for instance, a call to centralised ElasticSearch to upload logs for easy debugging
            err_msg = f"error retrieving data; unable to get post_id={post_id}; err={e}"
            print(err_msg)
            resp["error"] = err_msg
        return resp, status

    @route("list_all/<board_id>", methods=["GET"])
    def list_all(self, board_id):
        resp, status = {}, 500
        board_id = int(board_id)
        # TODO implement pagination for optimal experience
        posts = ModelBoard.query.filter(ModelPost.board_id == board_id).order_by(ModelPost.date_created.asc()).all()
        resp["board_id"] = board_id
        resp["posts"] = [post.repr() for post in posts]
        status = 200
        return resp, status

    @jwt_required
    def patch(self):
        """
        Edit post using post id
        """
        user_id = get_jwt_identity()
        post_id = int(request.form["post_id"])
        resp, status = {"updated": False, "post_id": post_id}, 500
        post = ModelPost.query.filter(ModelPost.post_id == post_id).one()
        board_id = None if post is None else post.board_id
        if post is None:
            resp["error"] = f"post_id={post_id} not found"
            status = 404
        elif not has_post_permission(user_id=user_id, board_id=board_id, post_id=post_id):
            resp["error"] = f"user_id={user_id} unauthorised to edit post_id={post_id} changes"
            status = 401
        else:
            post_title = request.form.get("post_title", post.post_title)
            if post_title == post.post_title:
                status = 304
            else:
                with Session(get_engine()) as session:
                    try:
                        session.query(ModelPost).filter(ModelPost.post_id == post_id).update({"post_title": post_title})
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        # TODO Insert logging - for instance, a call to ElasticSearch to upload logs for easy debugging
                        print(f"unable to update post_id={post_id} with new post_title={post_title}; err={e}")
        return resp, status

    @jwt_required
    def delete(self, post_id):
        """
        Delete board, post(s) and thread(s) associated with board
        """
        resp, status = {"deleted": False, "post_id": post_id}, 500
        with Session(get_engine()) as session:
            try:
                post = ModelBoard.query.filter(ModelPost.post_id == post_id).one()
                post_id = post.post_id
                board_id = post.board_id
                user_id = get_jwt_identity()
                if not has_post_permission(user_id=user_id, board_id=board_id, post_id=post_id):
                    err_msg = f"user_id={user_id} unauthorised to delete post_id={post_id} changes"
                    resp["error"] = err_msg
                    status = 401
                    raise Exception(err_msg)
                resp["deleted"] = True
                resp.update(post.repr())
                session.delete(post)
                session.commit()
                status = 200
            except Exception as e:
                session.rollback()
                # TODO Insert logging - for instance, a call to ElasticSearch to upload logs for easy debugging
                print(f"err={e} on attempt to delete board_id: {id}")
        return resp, status
