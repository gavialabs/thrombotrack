from typing import TypedDict
from .models import ThrombusType, Point

class AnnotateImagePayload(TypedDict):
    path: list[Point]
    thrombus_type: ThrombusType
