from datetime import datetime
import base64
import uuid
from marshmallow import fields, pre_dump, Schema
from marshmallow.fields import DateTime, Float, Integer, List, String, UUID
from marshmallow.validate import Length, OneOf, Range

from . import ma
from .models import Oxygenator, OxygenatorImage, AnnotationSession, Annotation
from .constants import OxygenatorType, AnnotationType
from app.dto import OxygenatorListQueryRow
from app.helpers import make_transparent_mask


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


class OxygenatorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Oxygenator

    # need to manually override enum fields, the auto-schema doesn't like them
    type = String(validate=OneOf([OxygenatorType.HLS, OxygenatorType.NAUTILUS]))
    thumbnail = Base64Field(dump_default=None)

    clot_area = Float(dump_default=None)
    fibrin_area = Float(dump_default=None)
    imaged_at = DateTime(dump_default=None)
    annotated_by = String(dump_default=None)

    @pre_dump
    def combine_oxygenator_and_last_imaged(
        self, data: Oxygenator | dict | OxygenatorListQueryRow, **kwargs
    ) -> dict:
        if isinstance(data, Oxygenator):
            return {
                "id": data.id,
                "name": data.name,
                "type": data.type.value,
            }

        if isinstance(data, dict):
            return data

        return {
            "id": data.id,
            "name": data.name,
            "type": data.type.value,
            "thumbnail": data.thumbnail,
            "clot_area": data.clot_area,
            "fibrin_area": data.fibrin_area,
            "imaged_at": data.imaged_at,
            "annotated_by": data.annotated_by,
        }


class OxygenatorImageSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OxygenatorImage

    cropped = Base64Field()
    thumbnail = Base64Field()
    current_annotation_session_id = UUID()
    mask = Base64Field()

    @pre_dump
    def combine_image_and_session(
        self,
        data: OxygenatorImage | tuple[OxygenatorImage, uuid.UUID | None, bytes],
        **kwargs
    ) -> OxygenatorImage | dict:
        if isinstance(data, tuple):
            return {
                "id": data[0].id,
                "cropped": data[0].cropped,
                "mimetype": data[0].mimetype,
                "current_annotation_session_id": data[1],
                "mask": make_transparent_mask(data[2]),
            }

        return data


class AnnotationSessionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AnnotationSession

    mask = Base64Field()
    imaged_at = DateTime()


class AnnotationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Annotation

    mask = Base64Field()
    path = List(
        List(Integer(validate=Range(min=0)), validate=Length(equal=2)),
        validate=Length(min=1),
    )
    type = String(
        validate=OneOf(
            [AnnotationType.CLOT, AnnotationType.FIBRIN, AnnotationType.ERASE]
        )
    )
