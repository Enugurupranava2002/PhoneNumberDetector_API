import requests
from db import db
from requests import Response
from flask import request, url_for
from uuid import uuid4
from lib.mailgun import Mailgun

from models.confirmation import ConfirmationModel

class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50))
    email = db.Column(db.String(50), nullable=False)
    confirmation = db.relationship("ConfirmationModel", lazy="dynamic",cascade="all, delete-orphan", back_populates="user")

    __table_args__ = (db.UniqueConstraint('username', 'email'), )

    def __init__(self, username: str, password: str, email: str):
        self.username = username
        self.password = password
        self.email = email

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username: str) ->"UserModel":
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, _id: int) ->"UserModel":
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_email(cls, email: str) ->"UserModel":
        return cls.query.filter_by(email=email).first()

    @property
    def most_recent_confirmation(self) -> "ConfirmationModel":
        return self.confirmation.order_by(db.desc(ConfirmationModel.expire_at)).first()

    def send_confirmation_email(cls) -> Response:
        otp_generated = uuid4().hex
        confirmation = cls.most_recent_confirmation
        confirmation.otp_generated = otp_generated
        confirmation.save_to_db()
        subject = "Registration confirmation."
        text = f"Dear Customer,\nWelcome, We thank you for using 'Api'\nYour Registration OTP code is: {otp_generated}"
        return Mailgun.send_email(
            email=[cls.email], 
            subject=subject,
            text=text
        )

    def user_confirmed_or_not(self):
        requests.get(url=request.url_root[:-1] + url_for(
            "confirmation", confirmation_id=self.most_recent_confirmation.id)
        )
