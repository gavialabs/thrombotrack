import datetime
import numpy as np
import cv2
from PIL import Image
from sqlalchemy import delete
from uuid import UUID, uuid4
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from ..utils.img_utils import *
from ..detection.oxygenator_detector import OxygenatorDetector
from ..segmentation.segmentor import Segmentor, AnnotationType
from ..models import (
    Oxygenator,
    OxygenatorImage,
    AnnotationSession,
    Annotation,
)
from .. import db
from ..helpers import decode_img, decode_mask, encode_img, encode_mask


def create_image(ecmo: Oxygenator, image_file: FileStorage):
    original_img = np.array(Image.open(image_file.stream), dtype=np.uint8)

    cropped, mm2_per_pixel = OxygenatorDetector(
        original_img, ecmo.type
    ).detect_oxygenator()

    thumbnail, _ = resize_with_scaling_factor(cropped, 512)

    ecmo_image = OxygenatorImage(
        ecmo_id=ecmo.id,
        filename=f"{uuid4().hex}_{secure_filename(image_file.filename)}",
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
    db.session.add(ecmo_image)
    db.session.flush()

    create_annotation_session(ecmo_image)

    db.session.commit()

    image_file.close()

    return ecmo_image


def create_annotation_session(image: OxygenatorImage) -> None:
    mask = np.zeros((image.width_cropped, image.height_cropped), dtype=np.bool)
    annotation_session = AnnotationSession(image_id=image.id, mask=encode_mask(mask))
    db.session.add(annotation_session)


def create_segmentation(
    ecmo_image: OxygenatorImage,
    annotation_session: AnnotationSession,
    path: list[list[int]],
    annotation_type: AnnotationType,
) -> bytes:
    img = decode_img(ecmo_image.cropped)
    session_mask = decode_mask(annotation_session.mask)

    segmentor = Segmentor(img, session_mask)

    clot_area = 0
    fibrin_area = 0

    if annotation_type == AnnotationType.ERASE:
        mask, clot_area, fibrin_area = segmentor.erase(path, annotation_session.segmentations)
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

    segmentation = Annotation(
        annotation_session_id=annotation_session.id,
        thrombus_type=annotation_type,
        path=path,
        mask=encode_mask(mask),
        clot_area=clot_area,
        fibrin_area=fibrin_area,
    )
    db.session.add(segmentation)
    db.session.commit()

    # convert bool mask to uint8 and make true pixels white
    display_mask = segmentor.img_mask.astype(np.uint8)
    display_mask[display_mask > 0] = 255

    # add alpha channel and make black pixels transparent so we can overlay mask
    display_mask = cv2.cvtColor(display_mask, cv2.COLOR_GRAY2RGBA)
    display_mask[display_mask[:, :, 0] == 0] = 0

    return encode_mask(display_mask)


def undo_segmentation(annotation_session: AnnotationSession) -> bytes:
    session_mask = decode_mask(annotation_session.mask)

    stmt = (
        db.select(Annotation)
        .where(Annotation.annotation_session_id == annotation_session.id)
        .order_by(Annotation.created_at.desc())
        .limit(1)
    )
    latest_segmentation: Annotation | None = db.session.execute(stmt).scalar()
    if latest_segmentation is None:
        display_mask = session_mask.astype(np.uint8)
        display_mask[display_mask > 0] = 255

        display_mask = cv2.cvtColor(display_mask, cv2.COLOR_GRAY2RGBA)
        display_mask[display_mask[:, :, 0] == 0] = 0

        return encode_mask(display_mask)

    latest_segmentation.undo = True

    segmentor = Segmentor(np.zeros(0), session_mask)
    segmentor.undo_segmentation(
        latest_segmentation.path, decode_mask(latest_segmentation.mask)
    )

    annotation_session.mask = encode_mask(segmentor.img_mask)

    if latest_segmentation.thrombus_type == AnnotationType.CLOT:
        annotation_session.clot_area -= latest_segmentation.area
    else:
        annotation_session.fibrin_area -= latest_segmentation.area

    db.session.commit()

    display_mask = segmentor.img_mask.astype(np.uint8)
    display_mask[display_mask > 0] = 255

    display_mask = cv2.cvtColor(display_mask, cv2.COLOR_GRAY2RGBA)
    display_mask[display_mask[:, :, 0] == 0] = 0

    return encode_mask(display_mask)


def redo_segmentation(annotation_session: AnnotationSession) -> bytes:
    session_mask = decode_mask(annotation_session.mask)

    stmt = (
        db.select(Annotation)
        .where(
            Annotation.annotation_session_id == annotation_session.id,
            Annotation.undo == True,
        )
        .order_by(Annotation.created_at)
        .limit(1)
    )
    last_undo_segmentation: Annotation | None = db.session.execute(stmt).scalar()
    if last_undo_segmentation is None:
        display_mask = session_mask.astype(np.uint8)
        display_mask[display_mask > 0] = 255

        display_mask = cv2.cvtColor(display_mask, cv2.COLOR_GRAY2RGBA)
        display_mask[display_mask[:, :, 0] == 0] = 0

        return encode_mask(display_mask)

    last_undo_segmentation.undo = False

    segmentor = Segmentor(np.zeros(0), session_mask)
    segmentor.redo_segmentation(
        last_undo_segmentation.path, decode_mask(last_undo_segmentation.mask)
    )

    annotation_session.mask = encode_mask(segmentor.img_mask)

    if last_undo_segmentation.thrombus_type == AnnotationType.CLOT:
        annotation_session.clot_area += last_undo_segmentation.area
    else:
        annotation_session.fibrin_area += last_undo_segmentation.area

    db.session.commit()

    display_mask = segmentor.img_mask.astype(np.uint8)
    display_mask[display_mask > 0] = 255

    display_mask = cv2.cvtColor(display_mask, cv2.COLOR_GRAY2RGBA)
    display_mask[display_mask[:, :, 0] == 0] = 0

    return encode_mask(display_mask)


def end_session(annotation_session: AnnotationSession, image: OxygenatorImage) -> None:
    annotation_session.ended_at = datetime.datetime.now()

    thumbnail = decode_img(image.thumbnail)
    mask = decode_mask(annotation_session.mask)
    resized_mask = resize_with_scaling_factor(mask, 512)

    # composite mask in some way, same as FE tho
    thumbnail[resized_mask] += [128, 128, 128]

    image.thumbnail_annotated = encode_img(thumbnail)

    # delete any segmentations from db that were marked as undo, since we will no longer redo them
    stmt = delete(Annotation).where(
        Annotation.annotation_session_id == annotation_session.id,
        Annotation.undo == True,
    )
    db.session.execute(stmt)

    db.session.commit()
