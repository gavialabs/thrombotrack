# Annotation session services

import datetime
import numpy as np
from flask import g
from sqlalchemy import delete

from app.segmentation.segmentor import Segmentor, AnnotationType
from app.models import (
    OxygenatorImage,
    AnnotationSession,
    Annotation,
)
from .. import db
from app.helpers import (
    decode_img,
    decode_mask,
    encode_img,
    encode_mask,
    overlay_mask,
)


def create_annotation_session(
    oxygenator_image: OxygenatorImage,
    last_annotation_session: AnnotationSession | None = None,
) -> AnnotationSession:
    """Creates an annotation session for an oxygenator image.

    Optionally copies annotations from a previous session.

    Args:
        oxygenator_image: OxygenatorImage to create annotation session for.


    Returns:
        New AnnotationSession.
    """
    if last_annotation_session is not None:
        # copy from last session
        annotation_session = AnnotationSession(
            oxygenator_image=oxygenator_image,
            mask=last_annotation_session.mask,
            clot_area=last_annotation_session.clot_area,
            fibrin_area=last_annotation_session.fibrin_area,
            user=g.get("user"),
        )

        db.session.add(annotation_session)
        db.session.flush()

        # copy each individual annotation as well
        copied_annotations = []
        for annotation in last_annotation_session.annotations:
            copied_annotations.append(
                Annotation(
                    annotation_session_id=annotation_session.id,
                    type=annotation.type,
                    path=annotation.path,
                    mask=annotation.mask,
                    clot_area=annotation.clot_area,
                    fibrin_area=annotation.fibrin_area,
                )
            )
        db.session.add_all(copied_annotations)
    else:
        mask = np.zeros(
            (oxygenator_image.width_cropped, oxygenator_image.height_cropped),
            dtype=np.bool,
        )
        annotation_session = AnnotationSession(
            oxygenator_image=oxygenator_image,
            mask=encode_mask(mask),
            user=g.get("user"),
        )
        db.session.add(annotation_session)

    db.session.commit()

    return annotation_session


def create_annotation(
    oxygenator_image: OxygenatorImage,
    annotation_session: AnnotationSession,
    path: list[list[int]],
    annotation_type: AnnotationType,
) -> None:
    """Creates an annotation for an oxygenator image.

    Uses Segmentor to segment the specified region of the image, updates annotation_session based
    on the area of the annotation, creates an annotation in the database, and returns the updated
    annotation session mask.

    Args:
        oxygenator_image: OxygenatorImage to create annotation for.
        annotation_session: Current AnnotationSession.
        path: List of xy coordinates defining annotation.
        annotation_type: Whether this is a clot, fibrin, or erasing.
    """
    img = decode_img(oxygenator_image.cropped)
    session_mask = decode_mask(annotation_session.mask)

    segmentor = Segmentor(img, session_mask)

    clot_area = 0
    fibrin_area = 0

    if annotation_type == AnnotationType.ERASE:
        mask, clot_area, fibrin_area = segmentor.erase(
            path, annotation_session.annotations
        )
        annotation_session.clot_area -= clot_area
        annotation_session.fibrin_area -= fibrin_area
    else:
        mask = segmentor.segment(path, annotation_type)
        area = int(np.count_nonzero(mask))

        if annotation_type == AnnotationType.CLOT:
            annotation_session.clot_area += area
            clot_area = area
        else:
            annotation_session.fibrin_area += area
            fibrin_area = area

    annotation_session.mask = encode_mask(segmentor.img_mask)

    annotation = Annotation(
        annotation_session_id=annotation_session.id,
        type=annotation_type,
        path=path,
        mask=encode_mask(mask),
        clot_area=clot_area,
        fibrin_area=fibrin_area,
    )
    db.session.add(annotation)
    db.session.commit()


def undo_annotation(annotation_session: AnnotationSession) -> None:
    """Undoes the last annotation in a session.

    If there are no annotations, does nothing. Otherwise, inverts the annotation mask and takes
    intersection with the session mask to remove its area. Does not allow undoing erase
    annotations.

    Args:
        annotation_session: Current AnnotationSession.
    """
    session_mask = decode_mask(annotation_session.mask)

    # get the last annotation that isn't undone and isn't an erase
    stmt = (
        db.select(Annotation)
        .where(
            Annotation.annotation_session_id == annotation_session.id,
            Annotation.undo == False,
            Annotation.type != AnnotationType.ERASE,
        )
        .order_by(Annotation.created_at.desc())
        .limit(1)
    )
    last_annotation: Annotation | None = db.session.execute(stmt).scalar()

    if last_annotation is None:
        return

    annotation_mask = decode_mask(last_annotation.mask)

    # perform the undo operation
    session_mask &= ~annotation_mask

    last_annotation.undo = True
    annotation_session.mask = encode_mask(session_mask)
    annotation_session.clot_area -= last_annotation.clot_area
    annotation_session.fibrin_area -= last_annotation.fibrin_area

    db.session.commit()


def redo_annotation(annotation_session: AnnotationSession) -> None:
    """Redoes the last undone annotation in a session.

    If there is no last undone annotation, does nothing. Otherwise, unions the session mask with
    the last undone annotation mask to add its area.

    Args:
        annotation_session: Current AnnotationSession.
    """
    session_mask = decode_mask(annotation_session.mask)

    # get the last undone annotation
    stmt = (
        db.select(Annotation)
        .where(
            Annotation.annotation_session_id == annotation_session.id,
            Annotation.undo == True,
        )
        .order_by(Annotation.created_at)
        .limit(1)
    )
    last_undo_annotation: Annotation | None = db.session.execute(stmt).scalar()

    if last_undo_annotation is None:
        return

    annotation_mask = decode_mask(last_undo_annotation.mask)

    # perform the redo operation
    session_mask |= annotation_mask

    last_undo_annotation.undo = False
    annotation_session.mask = encode_mask(session_mask)
    annotation_session.clot_area += last_undo_annotation.clot_area
    annotation_session.fibrin_area += last_undo_annotation.fibrin_area

    db.session.commit()


def end_annotation_session(annotation_session: AnnotationSession) -> None:
    """Ends an annotation session.

    Marks an annotation session as ended/saved, renders a new annotated thumbnail, and deletes any
    undone annotations from the database.

    Args:
        annotation_session: AnnotationSession to end.
    """
    annotation_session.ended_at = datetime.datetime.now()

    oxygenator_image = annotation_session.oxygenator_image

    thumbnail = decode_img(oxygenator_image.thumbnail)
    mask = decode_mask(annotation_session.mask)

    thumbnail_annotated = overlay_mask(mask, thumbnail)
    oxygenator_image.thumbnail_annotated = encode_img(thumbnail_annotated)

    # delete any segmentations from db that were marked as undo, since we will no longer redo them
    stmt = delete(Annotation).where(
        Annotation.annotation_session_id == annotation_session.id,
        Annotation.undo == True,
    )
    db.session.execute(stmt)

    db.session.commit()
