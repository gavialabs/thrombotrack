from typing import TypedDict

from .models import AnnotationType

class AnnotateImagePayload(TypedDict):
    path: list[list[int]]
    type: AnnotationType
