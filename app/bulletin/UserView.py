from flask_classful import FlaskView, request, route
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from passlib.hash import sha256_crypt
from sqlalchemy.orm import Session
import hashlib
import urllib.parse

from ..common.database_conn import get_engine
from .model.Model import ModelUser, UserRoleEnum


class UserView(FlaskView):
    @route("signup", methods=["POST"])
    def signup(self):
        """
        Create user
        """
        resp, status = {}, 500
        with Session(get_engine()) as session:
            email = request.form.get("email", None)
            username = request.form.get("username", None)
            try:
                salted_password = sha256_crypt.hash(request.form["password"])
                user = ModelUser(email=email,
                                 username=username,
                                 salted_password=salted_password,
                                 user_role=UserRoleEnum.GUEST)
                session.add(user)
                session.commit()
                session.refresh(user)
                resp["created"] = True
                resp.update(user.repr())
                session.commit()
                status = 201
            except Exception as e:
                session.rollback()
                # TODO Insert logging - for instance, a call to ElasticSearch to upload logs for easy debugging
                err_msg = f"unable to create user with email={email}, username={username}; err={e}"
                print(err_msg)
                resp = {
                    "created": False,
                    "email": email,
                    "username": username,
                    "datetime_created": None,
                    "error": err_msg,
                }
                status = 400
        return resp, status

    @route("login", methods=["POST"])
    def login(self):
        username = request.form.get("username", None)
        password = request.form.get("password", None)
        user = ModelUser.query.filter(ModelUser.username == username).one_or_none()
        if not user or not user.check_password(password):
            resp = {"error": "wrong username or password"}
            status = 401
            return resp, status
        resp = {"access_token": create_access_token(identity=user.user_id)}
        return resp, 200

    @route("set_role", methods=["PATCH"])
    @jwt_required
    def set_role(self):
        with Session(get_engine()) as session:
            current_user_id = get_jwt_identity()
            current_user = ModelUser.query.filter(ModelUser.user_id == current_user_id).one()
            current_user_role = current_user.user_role
            #
            target_role_raw = request.form.get("target_role", None)
            target_role = {
                "SUPERADMIN": UserRoleEnum.SUPERADMIN,
                "STAFF": UserRoleEnum.STAFF,
                "GUEST": UserRoleEnum.GUEST,
            }.get(target_role_raw, None)
            if target_role is None:
                return {"error": f"user_role={target_role_raw} unrecognised"}, 500
            target_user_id = request.form.get("username", None)
            target_user_id = int(target_user_id)
            target_user = ModelUser.query.filter(ModelUser.user_id == target_user_id).one()
            target_user_role = target_user.user_role
            # Disqualified
            if (current_user_role == UserRoleEnum.STAFF and target_user_role == UserRoleEnum.SUPERADMIN) or \
                    (current_user_role == UserRoleEnum.GUEST):
                return {"error": "unable to allow modification of permission"}, 500
            elif current_user_id == target_user_id:
                return {"error": "not allowed to change own role"}, 500
            try:
                session.query(ModelUser).filter(ModelUser.user_id == target_user_id).update(
                    {"user_role": target_role})
                session.commit()
                session.refresh(target_user)
                resp = target_user.repr()
                status = 200
            except Exception as e:
                session.rollback()
                resp, status = {"error": f"err={e}"}, 500
        return resp, status

    @route("avatar/userid/<user_id>/size/<size>", methods=["GET"])
    def avatar(self, user_id, size):
        default_avatar_url = "https://example.com/static/images/defaultavatar.jpg"
        user = ModelUser.query.filter(ModelUser.user_id == user_id).one_or_none()
        if not user:
            print("no such user")
            return {}, 500
        md5_hexdigest_email = hashlib.md5(user.email.lower().encode("utf-8")).hexdigest()
        parameters = urllib.parse.urlencode({"d": default_avatar_url, "s": str(size)}),
        return f"https://www.gravatar.com/avatar/{md5_hexdigest_email}?{parameters}"
