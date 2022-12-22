from ma import ma

from models.predict import PredictionModel

class PredictSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PredictionModel
        load_instance = True
        dump_only = ("id", )