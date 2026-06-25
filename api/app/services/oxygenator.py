# Oxygenator services

from sqlalchemy import func, Row
from uuid import UUID
from typing import Sequence

from app.models import (
    Oxygenator,
    OxygenatorImage,
    AnnotationSession,
    User,
)
from .. import db
from app.dto import AnnotationHistoryQueryRow, OxygenatorListQueryRow


def get_oxygenators() -> Sequence[Row[OxygenatorListQueryRow]]:
    """Queries a list of oxygenators.

    Returns:
        List of Rows containing oyxgenator id, name, type, last image thumbnail, last clot area,
        last fibrin area, and name of who annotated it last.
    """
    stmt = (
        db.select(
            Oxygenator.id,
            Oxygenator.name,
            Oxygenator.type,
            OxygenatorImage.thumbnail_annotated.label("thumbnail"),
            OxygenatorImage.created_at.label("imaged_at"),
            (AnnotationSession.clot_area * OxygenatorImage.mm2_per_pixel).label(
                "clot_area"
            ),
            (AnnotationSession.fibrin_area * OxygenatorImage.mm2_per_pixel).label(
                "fibrin_area"
            ),
            User.name.label("annotated_by"),
        )
        .outerjoin(
            OxygenatorImage,
            OxygenatorImage.id == Oxygenator.last_annotated_oxygenator_image_id,
        )
        .outerjoin(
            AnnotationSession,
            AnnotationSession.id == OxygenatorImage.last_annotation_session_id,
        )
        .outerjoin(AnnotationSession.user)
        .order_by(func.lower(Oxygenator.name))
    )
    results = db.session.execute(stmt).all()

    return results


def get_annotation_history(
    oxygenator_id: UUID,
) -> Sequence[Row[AnnotationHistoryQueryRow]]:
    """Gets a list of previous annotation values for an oxygenator.

    Args:
        oxygenator_id: ID of oxygenator to fetch annotation history for.

    Returns:
        Named tuple of image time, clot area, and fibrin area.
    """
    stmt = (
        db.select(
            OxygenatorImage.created_at.label("imaged_at"),
            (AnnotationSession.clot_area * OxygenatorImage.mm2_per_pixel).label(
                "clot_area"
            ),
            (AnnotationSession.fibrin_area * OxygenatorImage.mm2_per_pixel).label(
                "fibrin_area"
            ),
        )
        .join(
            AnnotationSession,
            AnnotationSession.id == OxygenatorImage.last_annotation_session_id,
        )
        .where(OxygenatorImage.oxygenator_id == oxygenator_id)
        .order_by(OxygenatorImage.created_at)
    )
    result = db.session.execute(stmt).all()

    return result

