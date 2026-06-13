# Oxygenator services file

import datetime
import numpy as np
import cv2
from flask import g, current_app as app
from PIL import Image
from sqlalchemy import delete, func, Row
from uuid import UUID
from werkzeug.datastructures import FileStorage

from ..utils.img_utils import *
from ..detection.oxygenator_detector import OxygenatorDetector
from ..segmentation.segmentor import Segmentor, AnnotationType
from ..models import (
    Oxygenator,
    OxygenatorImage,
    AnnotationSession,
    Annotation,
    User,
)
from .. import db
from ..helpers import (
    decode_img,
    decode_mask,
    encode_img,
    encode_mask,
    make_transparent_mask,
    overlay_mask,
)
from app.dto import OxygenatorListQueryRow


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


def create_image(
    oxygenator: Oxygenator, image_file: FileStorage
) -> tuple[OxygenatorImage, UUID]:
    """Crops an oxygenator image and starts an annotation session.

    Uses OxygenatorDetector to crop image and calculate conversion factor. Creates a thumbnail.
    Starts an annotation session.

    Args:
        oxygenator: Oxygenator to create the image for.
        image_file: File containing image of oxygenator.

    Returns:
        New OxygenatorImage object and ID of new AnnotationSession.
    """
    original_img = np.array(Image.open(image_file.stream), dtype=np.uint8)

    cropped, mm2_per_pixel = OxygenatorDetector(
        original_img, oxygenator.type
    ).detect_oxygenator()

    thumbnail, _ = resize_with_scaling_factor(cropped, 512)

    oxygenator_image = OxygenatorImage(
        oxygenator_id=oxygenator.id,
        mimetype=image_file.mimetype,
        original=encode_img(original_img),
        thumbnail=encode_img(thumbnail),
        cropped=encode_img(cropped),
        width_original=original_img.shape[0],
        height_original=original_img.shape[0],
        width_cropped=cropped.shape[0],
        height_cropped=cropped.shape[1],
        mm2_per_pixel=mm2_per_pixel,
    )
    db.session.add(oxygenator_image)
    db.session.flush()

    annotation_session = create_annotation_session(oxygenator_image)

    db.session.commit()

    image_file.close()

    return oxygenator_image, annotation_session.id


def create_annotation_session(
    oxygenator_image: OxygenatorImage, last_annotation_session: AnnotationSession | None
) -> AnnotationSession:
    """Create an annotation session for an oxygenator image.

    Args:
        oxygenator_image: OxygenatorImage to create annotation session for.

    Returns:
        New AnnotationSession.
    """
    if last_annotation_session is not None:
        annotation_session = AnnotationSession(
            oxygenator_image=oxygenator_image,
            mask=last_annotation_session.mask,
            clot_area = last_annotation_session.clot_area,
            fibrin_area = last_annotation_session.fibrin_area,
            user=g.get("user"),
        )

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
) -> bytes:
    """Creates an annotation for an oxygenator image.

    Uses Segmentor to segment the specified region of the image, updates annotation_session based
    on the area of the annotation, creates an annotation in the database, and returns the updated
    annotation session mask.

    Args:
        oxygenator_image: OxygenatorImage to create annotation for.
        annotation_session: Current AnnotationSession.
        path: List of xy coordinates defining annotation.
        annotation_type: Whether this is a clot, fibrin, or erasing.

    Returns:
        Updated mask for the annotation session for display in the app. Same size as the cropped
        oxygenator image, containing all annotations so far in this session in white with a
        transparent background.
    """
    img = decode_img(oxygenator_image.cropped)
    session_mask = decode_mask(annotation_session.mask)

    segmentor = Segmentor(img, session_mask)

    clot_area = 0
    fibrin_area = 0

    if annotation_type == AnnotationType.ERASE:
        mask, clot_area, fibrin_area = segmentor.erase(
            path, annotation_session.segmentations
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

    display_mask = make_transparent_mask(segmentor.img_mask)

    return encode_mask(display_mask)


def undo_annotation(annotation_session: AnnotationSession) -> bytes:
    """Undoes the last annotation in a session.

    If there is no last annotation, returns the current annotation session mask. Otherwise, inverts
    the annotation mask and takes intersection with the session mask to remove its area, and
    returns the updated session mask. Does not allow undoing erase annotations.

    Args:
        annotation_session: Current AnnotationSession.

    Returns:
        Updated annotation session mask.
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
        display_mask = make_transparent_mask(session_mask)
        return encode_mask(display_mask)

    annotation_mask = decode_mask(last_annotation.mask)

    # perform the undo operation
    session_mask &= ~annotation_mask

    last_annotation.undo = True
    annotation_session.mask = encode_mask(session_mask)
    annotation_session.clot_area -= last_annotation.clot_area
    annotation_session.fibrin_area -= last_annotation.fibrin_area

    db.session.commit()

    display_mask = make_transparent_mask(session_mask)
    return encode_mask(display_mask)


def redo_annotation(annotation_session: AnnotationSession) -> bytes:
    """Redoes the last undone annotation in a session.

    If there is no last undone annotation, returns the current annotation session mask. Otherwise,
    unions the session mask with the last undone annotation mask to add its area, and returns the
    updated session mask.

    Args:
        annotation_session: Current AnnotationSession.

    Returns:
        Updated annotation session mask.
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
        display_mask = make_transparent_mask(session_mask)
        return encode_mask(display_mask)

    annotation_mask = decode_mask(last_undo_annotation.mask)

    # perform the redo operation
    session_mask |= annotation_mask

    last_undo_annotation.undo = False
    annotation_session.mask = encode_mask(session_mask)
    annotation_session.clot_area += last_undo_annotation.clot_area
    annotation_session.fibrin_area += last_undo_annotation.fibrin_area

    db.session.commit()

    display_mask = make_transparent_mask(session_mask)
    return encode_mask(display_mask)


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


def get_annotation_history(oxygenator_id: UUID):
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


def get_images(oxygenator_id: UUID):
    """Queries a list of previous images for an oxygenator.

    Args:
        oxygenator_id: ID of oxygenator to fetch image history for.

    Returns:
        Query result iterator with rows of id, created_at, thumbnail.
    """
    stmt = (
        db.select(
            OxygenatorImage.id,
            OxygenatorImage.created_at,
            func.coalesce(
                OxygenatorImage.thumbnail_annotated, OxygenatorImage.thumbnail
            ).label("thumbnail"),
        )
        .where(OxygenatorImage.oxygenator_id == oxygenator_id)
        .order_by(OxygenatorImage.created_at)
    )

    return db.session.execute(stmt)


def get_image(
    oxygenator_image: OxygenatorImage, start_annotation_session: bool
) -> np.ndarray:
    last_annotation_session = None
    if oxygenator_image.last_annotation_session_id:
        last_annotation_session = db.get_or_404(
            AnnotationSession, oxygenator_image.last_annotation_session_id
        )

    # if start_annotation_session:
    #     annotation_session = create_annotation_session(oxygenator_image)

    cropped = decode_img(oxygenator_image.cropped)
    mask = decode_mask(last_annotation_session.mask)

    cropped_annotated = overlay_mask(mask, cropped)

    return cropped_annotated
