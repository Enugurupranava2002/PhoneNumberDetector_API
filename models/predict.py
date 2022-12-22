from db import db
import os
from typing import List
import cv2
import torch
import numpy as np
from flask_jwt_extended import get_jwt_identity

from lib.data_load import (
    Normalize, 
    Gray_scale_Image, 
    ToTensor, 
    Gray_scale_to_Binary, 
    BoundingBoxes, 
    Inversion
    )

data_transform = [
    Gray_scale_Image(), 
    Inversion(), 
    Gray_scale_to_Binary(), 
    BoundingBoxes(), 
    ToTensor()
    ]


from lib.ml_model import Net

class PredictionModel(db.Model):

    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(100), nullable=False)
    number_detected = db.Column(db.String(21), nullable=True)

    __table_args__ = (db.UniqueConstraint('image_path'), )

    @classmethod
    def predict_number(cls, filename: str) -> str:
        net = Net()
        path = "lib"
        model_file_name = "statedictmodelWith10EpochOperaAppliedOnEachDigitBatchSize320.pth"
        net.load_state_dict(torch.load(os.path.join(path, model_file_name)))
        img = cv2.imread(filename=filename)
        img_copy = img.copy()
        for j, fx in enumerate(data_transform):
            img_copy = fx(img_copy)
        img_copy = img_copy.type(torch.FloatTensor)
        number_predicted = net(img_copy)
        number_predicted = torch.argmax(number_predicted, dim=1)
        number_predicted = number_predicted.view(
            number_predicted.size()[0],
            -1
        )
        number_predicted = torch.reshape(number_predicted, (1, 10))
        return np.array2string((number_predicted.numpy())[0])

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_path(cls, filename: str) -> 'PredictionModel':
        path_extention = f"user_data_{get_jwt_identity()}/"
        image_path = path_extention + filename
        return cls.query.filter_by(image_path=image_path).first()

    @classmethod
    def find_all(cls) -> List["PredictionModel"]:
        return cls.query.all()

