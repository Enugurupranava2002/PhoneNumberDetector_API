import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URI = "sqlite:///data.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False
PROPAGATE_EXCEPTIONS = True
SECRET_KEY = os.getenv("APP_SECRET_KEY")
UPLOADED_IMAGES_DEST = os.path.join("app", os.path.join("static", "images"))