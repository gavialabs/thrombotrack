from flask import current_app as app
import base64
from marshmallow import fields, pre_dump, Schema
from marshmallow.fields import String
from marshmallow.validate import Length, OneOf, Range

from . import ma
from .models import Oxygenator, OxygenatorImage, AnnotationSession, Annotation
from .constants import OxygenatorType, AnnotationType


class Base64Field(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return base64.b64encode(value).decode("utf-8")

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        return base64.b64decode(value)


class MeSchema(Schema):
    authenticated = fields.Bool(required=True)
    user_id = fields.UUID()


class EcmoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Oxygenator

    # need to manually override enum fields, the auto-schema doesn't like them
    type = ma.String(validate=OneOf([OxygenatorType.HLS, OxygenatorType.NAUTILUS]))
    thumbnail = Base64Field()
    clot_area = ma.Float()
    fibrin_area = ma.Float()

    @pre_dump
    def combine_ecmo_and_latest_image(
        self, data: dict | tuple[Oxygenator, bytes, float, float], **kwargs
    ) -> dict:
        if isinstance(data, dict):
            return data

        return {
            "id": data[0].id,
            "name": data[0].name,
            "type": data[0].type.value,
            "thumbnail": data[1],
            "clot_area": data[2],
            "fibrin_area": data[3],
        }


class EcmoImageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OxygenatorImage

    cropped = Base64Field()
    thumbnail = Base64Field()


class AnnotationSessionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AnnotationSession

    mask = Base64Field()


class SegmentationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Annotation

    mask = Base64Field()
    path = ma.List(
        ma.List(ma.Integer(validate=Range(min=0)), validate=Length(equal=2)),
        validate=Length(min=1),
    )
    type = ma.String(
        validate=OneOf(
            [AnnotationType.CLOT, AnnotationType.FIBRIN, AnnotationType.ERASE]
        )
    )


class EcmoHistorySchema(ma.Schema):
    time = ma.DateTime()
    clot_area = ma.Float()
    fibrin_area = ma.Float()
