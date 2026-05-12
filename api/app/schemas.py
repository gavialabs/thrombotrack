from flask import current_app as app
import base64
from marshmallow import fields
from . import ma
from .models import Ecmo, Image, Segmentation


class Base64Field(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return base64.b64encode(value).decode("utf-8")

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        return base64.b64decode(value)


class EcmoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Ecmo


class EcmoImageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Image

    cropped = Base64Field()

class SegmentationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Segmentation
    
    mask = Base64Field()
