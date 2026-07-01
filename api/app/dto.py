"""Miscellaneous object typing with dataclasses."""

from datetime import datetime
from typing import NamedTuple, TypedDict

from app.models import AnnotationType
from app.constants import OxygenatorType


class OxygenatorListQueryRow(NamedTuple):
    id: str
    name: str
    type: OxygenatorType
    thumbnail: bytes | None
    clot_area: float
    fibrin_area: float
    imaged_at: datetime | None
    annotated_by: str | None


class AnnotationHistoryQueryRow(NamedTuple):
    imaged_at: datetime
    clot_area: float
    fibrin_area: float


class AnnotateImagePayload(TypedDict):
    path: list[list[int]]
    type: AnnotationType


class Coordinate(TypedDict):
    x: float
    y: float


class CropImagePayload(TypedDict):
    origin: Coordinate
    scale: float
