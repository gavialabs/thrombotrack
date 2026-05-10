from . import ma
from .models import Ecmo


class EcmoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Ecmo


class SegmentationSchema(ma.Schema):
    # corner1 = ma.List(ma.Integer(), validate=Length(equal=2), required=True)
    # corner2 = ma.List(ma.Integer(), validate=Length(equal=2), required=True)
    pass
