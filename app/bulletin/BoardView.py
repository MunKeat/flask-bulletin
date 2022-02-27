from flask_classful import FlaskView, request, route
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..common.database_conn import get_engine
from .model.Model import ModelBoard, ModelBoardModerator, BoardModerationStatusEnum, ModelUser, UserRoleEnum


def get_board_by_id_or_name(board_id, board_name):
    try:
        if board_id and board_name:
            board = ModelBoard.query.filter(and_(ModelBoard.board_id == board_id),
                                                (ModelBoard.board_name == board_name)).one()
        elif board_id:
            board = ModelBoard.query.filter(ModelBoard.board_id == board_id).one()
        elif board_name:
            board = ModelBoard.query.filter(ModelBoard.board_name == board_name).one()
        else:
            raise Exception("need to provide either board_id or board_name as input")
        return board
    except Exception as e:
        print(f"unable to retrieve board; error={e}")
        return None


class BoardView(FlaskView):
    @route("create", methods=["POST"])
    @jwt_required()
    def create(self):
        """
        Create board with unique name
        """
        board_name = request.form["board_name"]
        resp, status = {}, 500
        with Session(get_engine()) as session:
            try:
                board = ModelBoard(board_owner=get_jwt_identity(), board_name=board_name)
                session.add(board)
                session.commit()
                session.refresh(board)
                resp["created"] = True
                resp.update(board.repr())
                session.commit()
                status = 201
            except Exception as e:
                session.rollback()
                # TODO Insert logging - for instance, a call to ElasticSearch to upload logs for easy debugging
                print(f"unable to create board={board_name}; err={e}")
                resp = {
                    "created": False,
                    "board_id": None,
                    "datetime_created": None,
                }
                status = 400
        return resp, status

    def get(self, board_id):
        """
        Get list of post(s) associated with board,
        and board metadata (name, board owner, topic, list of moderators, datetime created)
        """
        resp, status = {}, 500
        # TODO Investigate if this truly does introduce READ_ISOLATION
        with Session(get_engine()) as _:
            try:
                board_id = int(board_id)
                board = ModelBoard.query.filter(ModelBoard.board_id == board_id).one()
                if board is None:
                    status = 404
                else:
                    resp = board.repr()
                    confirmed_moderators = ModelBoardModerator.query.filter(and_(ModelBoardModerator.board_id==board_id),
                                                                                 (ModelBoardModerator.status==BoardModerationStatusEnum.CONFIRMED)).all()
                    pending_moderators = ModelBoardModerator.query.filter(and_(ModelBoardModerator.board_id==board_id),
                                                                              (ModelBoardModerator.status==BoardModerationStatusEnum.PENDING)).all()
                    resp["confirmed_moderators"] = [moderator.user_id for moderator in confirmed_moderators]
                    resp["pending_moderators"] = [moderator.user_id for moderator in pending_moderators]
                    status = 200
            except ValueError as e:
                # TODO Insert logging - for instance, a call to centralised ElasticSearch to upload logs for easy debugging
                print(f"expected board_id to be integer; unable to cast board_id={board_id}; err={e}")
            except Exception as e:
                # TODO Insert logging - for instance, a call to centralised ElasticSearch to upload logs for easy debugging
                print(f"error retrieving data; unable to get board_id={board_id}; err={e}")
        return resp, status

    @jwt_required()
    def patch(self):
        """
        Edit board using board id
        """
        board_id = int(request.form["board_id"])
        resp, status = {"updated": False, "board_id": board_id}, 500
        board = ModelBoard.query.filter(ModelBoard.board_id == board_id).one()
        user = ModelUser.query.filter(ModelUser.user_id == get_jwt_identity()).one()
        board_name = request.form.get("board_name", board.board_name)
        if not (board.board_owner == get_jwt_identity() or user.user_role in [UserRoleEnum.SUPERADMIN,
                                                                              UserRoleEnum.STAFF]):
            raise Exception(f"user={user.username} not allowed to edit board_id={board.board_id}")
        if board_name == board.board_name:
            status = 304
        else:
            with Session(get_engine()) as session:
                try:
                    session.query(ModelBoard).filter(ModelBoard.board_id == board_id).update({"board_name": board_name})
                    session.commit()
                    resp["updated"] = True
                    status = 200
                except Exception as e:
                    session.rollback()
                    # TODO Insert logging - for instance, a call to ElasticSearch to upload logs for easy debugging
                    print(f"unable to update board_id={board_id} with new board_name={board_name}; err={e}")
        return resp, status

    @jwt_required()
    def delete(self, board_id):
        """
        Delete board, post(s) and thread(s) associated with board
        """
        resp, status = {"deleted": False, "board_id": board_id}, 500
        with Session(get_engine()) as session:
            try:
                user = ModelUser.query.filter(ModelUser.user_id == get_jwt_identity()).one()
                board = ModelBoard.query.filter(ModelBoard.board_id == board_id)
                if not (board.board_owner == get_jwt_identity() or user.user_role in [UserRoleEnum.SUPERADMIN, UserRoleEnum.STAFF]):
                    raise Exception(f"user={user.username} not allowed to delete board_id={board.board_id}")
                resp["deleted"] = True
                resp.update(board.repr())
                session.delete(board)
                session.commit()
                status = 200
            except Exception as e:
                session.rollback()
                # TODO Insert logging - for instance, a call to ElasticSearch to upload logs for easy debugging
                print(f"err={e} on attempt to delete board_id: {board_id}")
        return resp, status

    @route("list_moderation/<user_id>", methods=["GET"])
    @jwt_required()
    def list_moderation(self, user_id=None):
        """
        List all moderation invites
        """
        resp, status = {}, 500
        if user_id:
            moderation = ModelBoardModerator.query.filter((ModelBoardModerator.user_id == user_id)).all()
        else:
            moderation = ModelBoardModerator.query.all()
        resp["moderation"] = [moderator.repr() for moderator in moderation]
        status = 200
        return resp, status

    @route("accept_moderation", methods=["PATCH"])
    @jwt_required()
    def accept_moderation(self):
        board_id = int(request.form["board_id"])
        proposed_moderator = int(request.form["proposed_moderator"])
        resp, status = {"updated": False, "board_id": board_id}, 500
        with Session(get_engine()) as session:
            try:
                if get_jwt_identity() != proposed_moderator:
                    return {"error": f"not allowed to acccept moderation for user_id={proposed_moderator}"}, 400
                if ModelBoardModerator.query.filter(and_(ModelBoardModerator.user_id == proposed_moderator), (ModelBoardModerator.board_id==board_id)).count() == 0:
                    return {"error": f"no moderation exists for board_id={board_id}, moderator_id={proposed_moderator}"}, 404
                session.query(ModelBoardModerator).filter(and_(ModelBoardModerator.user_id == proposed_moderator),
                                                               (ModelBoardModerator.board_id == board_id)).update({"status": BoardModerationStatusEnum.CONFIRMED})
                session.commit()
                resp["updated"] = True
                status = 200
            except Exception as e:
                session.rollback()
                resp["error"] = str(e)
        return resp, status

    @route("invite_moderation", methods=["POST"])
    @jwt_required()
    def invite_moderation(self):
        # Check invite self is not allowed
        with Session(get_engine()) as session:
            board_id = int(request.form["board_id"])
            proposed_moderator = int(request.form["proposed_moderator"])
            if proposed_moderator == get_jwt_identity():
                return {"error": f"not allowed to invite self as moderator for board_id={board_id}"}, 422
            if ModelBoardModerator.query.filter(and_(ModelBoardModerator.user_id == proposed_moderator), (ModelBoardModerator.board_id==board_id)).count() > 0:
                return {"error": f"moderation already exists for board_id={board_id}, moderator_id={proposed_moderator}"}, 409
            moderator = ModelBoardModerator(board_id=board_id, user_id=proposed_moderator, status=BoardModerationStatusEnum.PENDING)
            session.add(moderator)
            session.commit()
            session.refresh(moderator)
        return moderator.repr(), 201

    @route("revoke_moderation", methods=["DELETE"])
    @jwt_required()
    def revoke_moderation(self):
        with Session(get_engine()) as session:
            try:
                board_id = int(request.args["board_id"])
                proposed_moderator = int(request.form["proposed_moderator"])
                resp, status = {"deleted": False, "board_id": board_id, "proposed_moderator": proposed_moderator}, 500
                user = ModelUser.query.filter(ModelUser.user_id == get_jwt_identity()).one()
                board = ModelBoard.query.filter(ModelBoard.board_id == board_id).one()
                if not (board.board_owner == get_jwt_identity() or user.user_role in [UserRoleEnum.SUPERADMIN, UserRoleEnum.STAFF]):
                    raise Exception("not allowed to revoke moderation")
                moderator = ModelBoardModerator.query.filter(and_(ModelBoardModerator.user_id==proposed_moderator), (ModelBoardModerator.board_id==board_id))
                resp["deleted"] = True
                resp.update(moderator.repr())
                session.delete(moderator)
                session.commit()
                status = 200
            except Exception as e:
                session.rollback()
                # TODO Insert logging - for instance, a call to ElasticSearch to upload logs for easy debugging
                print(f"err={e} on attempt to delete moderation, board_id={board_id}, proposed_moderator={proposed_moderator}")
        return resp, status

    @route("list_all", methods=["GET"])
    def list_all(self):
        boards = ModelBoard.query.all()
        resp = {
            "boards": [board.repr() for board in boards]
        }
        status = 200
        return resp, status
