import hmac
from flask_restful import Resource
from time import time
import traceback
from flask import request

from models.confirmation import ConfirmationModel
from schemas.confirmation import ConfirmationSchema
from lib.mailgun import Mailgun
from models.user import UserModel

CONFIRMATION_NOT_FOUND = "Confirmation reference not found."
CONFIRMATION_EXPIRED = "Confirmation OTP has expired. Please confirm again."
CONFIRMATION_HAS_CONFIRMED = "you had successfully confirmed. No need to confirm again."
THANK_YOU = "Thanks '{}' for confirming."
USER_NOT_FOUND = "User not found."
CONFIRMATION_RESEND_SUCCESSFUL = "New confirmation OTP has been sent to your mail address. Please check."
CONFIRMATION_RESEND_FAIL = "Confirmation resend mail has failed."

confirmation_schema = ConfirmationSchema()
mailgun_class = Mailgun()

class Confirmation(Resource):

    @classmethod
    def get(cls, confirmation_id: str):
        confirmation = ConfirmationModel.find_by_id(confirmation_id)
        if not confirmation:
            return {"message": CONFIRMATION_NOT_FOUND}, 404
        if confirmation.expired:
            return {"message": CONFIRMATION_EXPIRED}, 400
        if confirmation.confirmed:
            return {"message": CONFIRMATION_HAS_CONFIRMED}, 400

        if hmac.compare_digest(confirmation.otp_entered, confirmation.otp_generated):
            confirmation.confirmed = True
            confirmation.save_to_db()
            return {"message": THANK_YOU.format(confirmation.user.username)}
        return {"message": "OTP entered is invalid."}

class UserEnterOtp(Resource):
    @classmethod
    def post(cls, user_name: str):
        user = UserModel.find_by_username(user_name)
        confirmation = user.most_recent_confirmation
        # if confirmation is None:
        #     data_json = request.get_json()
        #     confirmation.otp_entered = data_json["entered_otp"]
        #     confirmation.save_to_db()
        #     return {"message": "OTP entered successfully."}, 201
        if not confirmation:
            return {"message": CONFIRMATION_NOT_FOUND}, 404
        if confirmation.confirmed:
            return {"message": CONFIRMATION_HAS_CONFIRMED}, 400
        if confirmation.expired:
            return {"message": CONFIRMATION_EXPIRED}, 400

        data_json = request.get_json()
        confirmation.otp_entered = data_json["entered_otp"]
        confirmation.save_to_db()
        if confirmation.is_otp_same:
            return {"message": "OTP entered is correct."}, 201
        return {"message": "OTP entered is incorrect."}, 201

class ConfirmationByUser(Resource):

    @classmethod
    def get(cls, user_name: str):
        user = UserModel.find_by_username(user_name)
        if not user:
            return {"message": USER_NOT_FOUND}, 404
        return (
            {
                "current_time": int(time()),
                "confirmation": [
                    confirmation_schema.dump(each)
                    for each in user.confirmation.order_by(ConfirmationModel.expire_at).all()
                ],
            }, 200,
        )

    @classmethod
    def post(cls, user_name: str):
        user = UserModel.find_by_username(user_name)
        if user is None:
            return {"message": USER_NOT_FOUND}, 404

        try:
            confirmation = user.most_recent_confirmation
            if confirmation:
                if confirmation.confirmed:
                    return {"message": CONFIRMATION_HAS_CONFIRMED}, 400
                confirmation.force_to_expire()
            new_confirmation = ConfirmationModel(user.id)
            new_confirmation.save_to_db()
            user.send_confirmation_email()
            return {"message": CONFIRMATION_RESEND_SUCCESSFUL}, 201
        except mailgun_class.MailGunException as e:
            return {"message": str(e)}, 500
        except:
            traceback.print_exc()
            return {"message": CONFIRMATION_RESEND_FAIL}, 500
