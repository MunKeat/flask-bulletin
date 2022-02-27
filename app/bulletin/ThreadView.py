from flask_classful import FlaskView, request, route
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..common.database_conn import get_engine
from .PostView import get_post_by_id
from .model.Model import ModelThread, ModelPost, ModelBoard, ModelBoardModerator, ModelUser, UserRoleEnum


def has_thread_permission(user_id, post_id, thread_id=None):
    user = ModelUser.query.filter(ModelUser.user_id == user_id).one()
    post = ModelPost.query.filter(ModelPost.post_id == post_id).one()
    board_id = post.board_id
    board = ModelBoard.query.filter(ModelBoard.board_id == board_id).one()
    is_superuser_or_staff = (user.user_role in [UserRoleEnum.SUPERADMIN, UserRoleEnum.STAFF])
    is_board_admin = (board.board_owner == user_id)
    is_post_admin = (post.post_owner == user_id)
    if is_superuser_or_staff or is_board_admin or is_post_admin:
        return True
    is_board_moderator = (ModelBoardModerator.query.filter(and_(ModelBoardModerator.board_id==board_id), (ModelBoardModerator.user_id==user_id)).count() == 1)
    if thread_id is None:
        return is_board_moderator
    thread = ModelThread.query.filter(ModelThread.thread_id==thread_id).one()
    is_thread_owner = (thread.thread_owner == user_id)
    return is_thread_owner


class ThreadView(FlaskView):
    @route("create", methods=["POST"])
    @jwt_required
    def create(self):
        """
        Create thread
        """
        resp, status = {}, 500
        with Session(get_engine()) as session:
            try:
                user_id = get_jwt_identity()
                post_id = request.form.get("post_id", None)
                post_id = None if post_id is None else int(post_id)
                post = get_post_by_id(post_id)
                thread_content = request.form.get("thread_content", None)
                if post is None:
                    return resp, status
                elif not thread_content:
                    err_msg = f"thread_content={thread_content} is invalid"
                    print(err_msg)
                    resp["error"] = err_msg
                    return resp, status
                elif not has_thread_permission(user_id=user_id, post_id=post_id):
                    err_msg = f"user_id={user_id} not allowed to create thread in post_id={post_id}"
                    print(err_msg)
                    resp["error"] = err_msg
                    return resp, status
                thread = ModelThread(thread_owner=user_id, post_id=post_id, thread_content=thread_content)
                session.add(thread)
                session.commit()
                session.refresh(thread)
                resp["created"] = True
                resp.update(thread.repr())
                session.commit()
                status = 201
            except Exception as e:
                session.rollback()
                # TODO Insert logging - for instance, a call to ElasticSearch to upload logs for easy debugging
                print(f"unable to create thread={thread_content} in post_id={post_id}; err={e}")
                resp = {
                    "created": False,
                    "post_id": post_id,
                    "thread_id": None,
                    "datetime_created": None,
                }
                status = 400
        return resp, status

    def get(self, thread_id):
        """
        Get post,
        """
        resp, status = {}, 500
        try:
            thread_id = int(thread_id)
            thread = ModelThread.query.filter(ModelThread.thread_id == thread_id).one()
            if thread is None:
                status = 404
            else:
                resp = thread.repr()
                status = 200
        except ValueError as e:
            # TODO Insert logging - for instance, a call to centralised ElasticSearch to upload logs for easy debugging
            print(f"expected thread_id to be integer; unable to cast thread_id={thread_id}; err={e}")
        except Exception as e:
            # TODO Insert logging - for instance, a call to centralised ElasticSearch to upload logs for easy debugging
            print(f"error retrieving data; unable to get thread_id={thread_id}; err={e}")
        return resp, status

    @route("list_all/<post_id>", methods=["GET"])
    def list_all(self, post_id):
        resp, status = {}, 500
        post_id = int(post_id)
        # TODO implement pagination for optimalised experience
        threads = ModelThread.query.filter(ModelThread.post_id == post_id).order_by(ModelThread.date_created.asc()).all()
        resp["post_id"] = post_id
        resp["posts"] = [thread.repr() for thread in threads]
        status = 200
        return resp, status

    @jwt_required
    def patch(self):
        """
        Edit thread using thread id
        """
        with Session(get_engine()) as session:
            user_id = get_jwt_identity()
            thread_id = int(request.form["thread_id"])
            resp, status = {"updated": False, "thread_id": thread_id}, 500
            thread = ModelThread.query.filter(ModelThread.thread_id == thread_id).one()
            if thread is None:
                status = 404
            elif not has_thread_permission(user_id=user_id, post_id=thread.post_id, thread_id=thread_id):
                err_msg = f"user_id={user_id} not allowed to modify thread_id={thread_id} in post_id={thread.post_id}"
                print(err_msg)
                resp["error"] = err_msg
                return resp, status
            else:
                thread_content = request.form.get("thread_content", thread.thread_content)
                if thread_content == thread.thread_content:
                    status = 304
                else:
                    try:
                        session.query(ModelThread).filter(ModelThread.thread_id == thread_id).update({"thread_content": thread_content})
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        # TODO Insert logging - for instance, a call to ElasticSearch to upload logs for easy debugging
                        print(f"unable to update board_id={thread_id} with new thread_content={thread_content}; err={e}")
        return resp, status

    @jwt_required
    def delete(self, thread_id):
        """
        Delete board, post(s) and thread(s) associated with board
        """
        resp, status = {"deleted": False, "post_id": thread_id}, 500
        with Session(get_engine()) as session:
            try:
                user_id = get_jwt_identity()
                thread = ModelThread.query.filter(ModelThread.thread_id == thread_id).one()
                if not has_thread_permission(user_id=user_id, post_id=thread.post_id, thread_id=thread_id):
                    err_msg = f"user_id={user_id} not allowed to delete thread_id={thread_id} in post_id={thread.post_id}"
                    print(err_msg)
                    resp["error"] = err_msg
                    raise Exception(err_msg)
                resp["deleted"] = True
                resp.update(thread.repr())
                session.delete(thread)
                session.commit()
                status = 200
            except Exception as e:
                session.rollback()
                # TODO Insert logging - for instance, a call to ElasticSearch to upload logs for easy debugging
                print(f"err={e} on attempt to delete thread_id={thread_id}")
        return resp, status
