import traceback
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from flask import request
from uuid import uuid4
import os
from flask_uploads import UploadNotAllowed

from schemas.image import ImageSchema
from lib import image_helper

image_schema = ImageSchema()

IMAGE_UPLOADED = "Image '{}' uploaded successfully."
IMAGE_ILLEGAL_EXTENSION = "Extension '{}' is illegal."
ERROR_IN_CREATING_FOLDER = "Error occured in creating the folder!"

class ImageUpload(Resource):
    @classmethod
    @jwt_required(fresh=True)
    def post(cls):
        try:
            data = image_schema.load(request.files)
        except:
            traceback.print_exc()
            return {"message": "Error in loading data."}
        try:
            folder = f"user_data_{get_jwt_identity()}"
        except:
            traceback.print_exc()
            return {"message": ERROR_IN_CREATING_FOLDER}
        filename = str(uuid4().hex) + "."
        try:
            image_path = image_helper.save_image(data['image'], folder, filename)
            basename = image_helper.get_basename(image_path)
            # numberString = np.array2string(ml_model.predict(f"/tmp/images/user_data/{basename}"))
            return {
                "message": IMAGE_UPLOADED.format(basename)
                }, 201
        except UploadNotAllowed:
            extension = image_helper.get_extension(data['image'])
            return {"message": IMAGE_ILLEGAL_EXTENSION.format(extension)}, 401

class UserImageList(Resource):
    @classmethod
    @jwt_required(fresh=True)
    def get(cls, user_id: int):
        list_of_files = []
        folder = f"app/static/images/user_data_{user_id}"
        for root, directories, file in os.walk(folder):
            list_of_files.append(file)
        return {
            "images_list": list_of_files
        }
