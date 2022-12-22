from requests import Response, post
from typing import List
import os
from dotenv import load_dotenv

FAILED_LOAD_API_KEY = "Failed to load 'MailGun Api Key'."
FAILED_LOAD_DOMAIN = "Failed to load 'MainGun Domain.'"
ERROR_SENDING_EMAIL = "Error occured while sending an email."

load_dotenv()

class Mailgun:

    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
    FROM_EMAIL = os.getenv("FROM_EMAIL")

    class MailGunException(Exception):
        def __init__(self, message: str) -> None:
            super().__init__(message)

    @classmethod
    def send_email(cls, email: List[str], subject: str, text: str) -> Response:
        
        if cls.MAILGUN_API_KEY is None:
            raise cls.MailGunException(FAILED_LOAD_API_KEY)
        
        if cls.MAILGUN_DOMAIN is None:
            raise cls.MailGunException(FAILED_LOAD_DOMAIN)
        
        response = post(
            f"https://api.mailgun.net/v3/{cls.MAILGUN_DOMAIN}/messages",
            auth=("api", cls.MAILGUN_API_KEY),
            data={
                "from": f"{cls.FROM_EMAIL}",
                "to": email,
                "subject": subject,
                "text": text
            },
        )

        if response.status_code != 200:
            return cls.MailGunException(ERROR_SENDING_EMAIL)

        return response
