from flask import Flask, jsonify, make_response
from flask_restful import Api
from marshmallow import ValidationError
import dotenv
import torch
import os
from flask_uploads import configure_uploads, patch_request_class
from flask_jwt_extended import JWTManager, get_jwt

from db import db
from ma import ma
from resources.user import (
    UserRegister, 
    UserLogin, 
    UserLogout,
    User,
    UserList
    )
from resources.image import ImageUpload, UserImageList
from resources.predict import Predict, PredictionList
from resources.confirmation import ConfirmationByUser, Confirmation, UserEnterOtp
from lib.image_helper import IMAGE_SET
from blocklist import BLOCKLIST

LOGIN_REQUIRED = "Timed out 'Relogin' required!"
NO_ACCESS_TOKEN = "Requested does not contain an access token."
AUTHORIZATION_REQUIRED = "authorization_required."
TOKEN_REVOKED = "You had logged out already! Please login again."
FRESH_TOKEN_REQUIRED = "Please login again!"

app = Flask(__name__)

dotenv.load_dotenv(".env", verbose=True)
app.config.from_object("default_config")
app.config.from_envvar("APPLICATION_SETTINGS")

patch_request_class(app,10*1024*1024)
configure_uploads(app, IMAGE_SET)

api = Api(app)

jwt = JWTManager(app)

@app.before_first_request
def create_tables():
    db.create_all()

@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify(err.messages), 400

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    return jwt_payload["jti"] in BLOCKLIST

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': TOKEN_REVOKED
    })

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    if check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jsonify({
            "error" : LOGIN_REQUIRED
        }), 400
    else:
        return jsonify({
            'error': 'Session expired Login Required!'
        })

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({
        'error': AUTHORIZATION_REQUIRED
    })

@jwt.needs_fresh_token_loader
def token_not_fresh_callback(jwt_header, jwt_payload):
    return jsonify({
        "error" : 'fresh_token_required'
    }), 401

api.add_resource(UserRegister, "/register")
api.add_resource(ImageUpload, "/image_upload")
api.add_resource(UserImageList, "/image_list/<int:user_id>")
api.add_resource(Predict, "/predict/<string:filename>")
api.add_resource(PredictionList, "/predictions")
api.add_resource(UserLogin, "/login")
api.add_resource(UserLogout, "/logout")
api.add_resource(ConfirmationByUser, "/confirmByUser/<string:user_name>")
api.add_resource(Confirmation, "/confirm_otp/<string:confirmation_id>")
api.add_resource(UserEnterOtp, "/confirm_otp/<string:user_name>")
api.add_resource(User, "/user/<string:user_name>")
api.add_resource(UserList, "/users")

if __name__ == '__main__':
    db.init_app(app)
    ma.init_app(app)
    app.run(port=5000, debug=True)