from flask import current_app as app
import base64
from marshmallow import fields, pre_dump
from marshmallow.validate import Length, OneOf, Range

from . import ma
from .models import Ecmo, EcmoType, Image, AnnotationSession, Segmentation, ThrombusType


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

    # need to manually override enum fields, the auto-schema doesn't like them
    type = ma.String(validate=OneOf([EcmoType.GETINGE.value, EcmoType.NAUTILUS.value]))
    thumbnail = Base64Field()
    total_annotated_area = ma.Float()

    @pre_dump
    def combine_ecmo_and_latest_image(self, data: tuple[Ecmo, bytes, float], **kwargs) -> dict:
        return {
            "id": data[0].id,
            "name": data[0].name,
            "type": data[0].type.value,
            "thumbnail": data[1],
            "total_annotated_area": data[2],
        }


class EcmoImageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Image

    cropped = Base64Field()


class AnnotationSessionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AnnotationSession

    mask = Base64Field()


class SegmentationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Segmentation

    mask = Base64Field()
    path = ma.List(
        ma.List(ma.Integer(validate=Range(min=0)), validate=Length(equal=2)),
        validate=Length(min=1),
    )
    thrombus_type = ma.String(validate=OneOf([ThrombusType.CLOT, ThrombusType.FIBRIN]))
