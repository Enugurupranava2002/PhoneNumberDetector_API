import hmac
import traceback
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity, jwt_required
from flask_restful import Resource
from flask import request
from models.confirmation import ConfirmationModel

from models.user import UserModel
from schemas.user import UserSchema
from blocklist import BLOCKLIST
from lib.mailgun import Mailgun

user_schema = UserSchema()

USER_ALREADY_EXIST = "A user with this username already exists."
REGISTERED_USER_SUCCESSFULLY = "User registered successfully."
PASSWORD_CANNOT_LEFT_BLANK = "Password required!"
USERNAME_CANNOT_LEFT_BLANK = "Username required!"
INVALID_CREDENTIALS = "Invalid credentials!"
USER_LOGGED_OUT = "User logged out successfully."
EMAIL_ALREADY_EXIST = "A user with this email already exists."
USER_NOT_CONFIRMED = "User '{}' was not confirmed yet!"
ERROR_IN_REGISTERING_USER = "Error occured in registering user."
USER_NOT_FOUND = "User with username '{}' is not found."
USER_DELETED = "User deleted successfully."

class UserRegister(Resource):

    def post(self):
        user_json = request.get_json()
        user = user_schema.load(user_json)

        if user.username == "":
            return {"message": USERNAME_CANNOT_LEFT_BLANK}, 400

        if user.password == "":
            return {"message": PASSWORD_CANNOT_LEFT_BLANK}, 400

        if UserModel.find_by_username(user.username):
            return {"message": USER_ALREADY_EXIST}, 400

        if UserModel.find_by_email(user.email):
            return {"message": EMAIL_ALREADY_EXIST}, 400
            
        try:
            user.save_to_db()
            confirmation = ConfirmationModel(user.id)
            confirmation.save_to_db()
            user.send_confirmation_email()
            return {"message": REGISTERED_USER_SUCCESSFULLY}, 201
        except Mailgun.MailGunException as e:
            user.delete_from_db(user)
            return {"message": str(e)}, 500
        except:
            traceback.print_exc()
            user.delete_from_db()
            return {"message": ERROR_IN_REGISTERING_USER}

class UserLogin(Resource):

    @classmethod
    def post(cls):
        user_json = request.get_json()
        user_data = user_schema.load(user_json)
        user = UserModel.find_by_username(user_data.username)
        if user and hmac.compare_digest(user.password, user_data.password):
            confirmation = user.most_recent_confirmation
            if confirmation.is_otp_same:
                confirmation.confirmed = True
                confirmation.save_to_db()
            if confirmation and confirmation.confirmed:
                access_token = create_access_token(identity=user.id, fresh=True)
                refresh_token = create_refresh_token(user.id)
                return {"access_token": access_token, "refresh_token": refresh_token}, 200
            return {"message": USER_NOT_CONFIRMED.format(user.username)}, 400 
        return {
            "message": INVALID_CREDENTIALS
        }

class UserLogout(Resource):
    @classmethod
    @jwt_required()
    def post(cls):
        jti = get_jwt()["jti"]
        user_id = get_jwt_identity()
        BLOCKLIST.add(jti)
        return {"message": USER_LOGGED_OUT.format(user_id)}, 200

class User(Resource):
    @classmethod
    def delete(cls, user_name: str):
        user = UserModel.find_by_username(username=user_name)
        if not user:
            return {"message": USER_NOT_FOUND.format(user_name)}, 404
        user.delete_from_db()
        return {"message": USER_DELETED}, 200

class UserList(Resource):
    @classmethod
    def get(cls):
        users = [user.username for user in UserModel.query.all()]
        return {'user_names': users}, 200