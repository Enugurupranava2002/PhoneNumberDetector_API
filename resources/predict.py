from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
import traceback
import os

from models.predict import PredictionModel
from schemas.predict import PredictSchema
from lib import image_helper

IMAGE_ILLEGAL_FILENAME = "Illegal '{}' filename."
IMAGE_NOT_FOUND = "There doesn't exist any file with '{}', as filename."
CHANGED_SUCCESSFULLY = "Changes made successfully."
ERROR_OCCURED = "Encountered an error!"
ERROR_IN_FINDING_PATH_EXTENTION = "Error in finding path extension."

predict_schema = PredictSchema()
predict_list_schema = PredictSchema(many=True)

class Predict(Resource):

    @classmethod
    @jwt_required(fresh=True)
    def get(cls, filename: str):
        try:
            path_extention = f"app/static/images/user_data_{get_jwt_identity()}/"
        except:
            traceback.print_exc()
            return {"message": ERROR_IN_FINDING_PATH_EXTENTION}
        if not image_helper.is_filename_safe(filename):
            return {"message": IMAGE_ILLEGAL_FILENAME.format(filename)}
        if image_helper.find_image_any_format(filename=filename.split(".")[0], folder=f"user_data_{get_jwt_identity()}") is None:
            return {"message": IMAGE_NOT_FOUND.format(filename)}
        try:
            image_path = path_extention + filename
            number_detected = PredictionModel.predict_number(filename=image_path)
            relative_image_path = f"user_data_{get_jwt_identity()}/" + filename
            predict_obj = predict_schema.load({
                "image_path": relative_image_path,
                "number_detected": number_detected
            })
            PredictionModel.save_to_db(predict_obj)
            image_helper.upload_to_gd(filename, image_path, get_jwt_identity())
            os.remove(image_path)
            return jsonify(predict_schema.dump(predict_obj))
            # return {"message":image_path, "number_detected": number_detected}
        except FileNotFoundError:
            return {"message": IMAGE_NOT_FOUND.format(filename)}

    @classmethod
    @jwt_required(fresh=True)
    def put(cls, filename: str):
        # return {"messsage": "Entered to put."}
        if not image_helper.is_filename_safe(filename):
            return {"message": IMAGE_ILLEGAL_FILENAME.format(filename)}
        predict_obj = PredictionModel.find_by_path(filename = filename)
        try:
            data = request.get_json()
            predict_obj.number_detected = data["correct_number"]
            predict_obj.save_to_db()
            return {"message": CHANGED_SUCCESSFULLY}
        except FileNotFoundError:
            return {"message": IMAGE_NOT_FOUND.format(filename)}
        except:
            traceback.print_exc()
            return {"message": ERROR_OCCURED}

class PredictionList(Resource):
    @classmethod
    def get(cls):
        return {
            "predictions": predict_list_schema.dump(PredictionModel.find_all())
        }, 200
