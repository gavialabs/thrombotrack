import io
import numpy as np
import cv2
from flask import current_app as app
from PIL import Image
from uuid import UUID, uuid4
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from ..utils.img_utils import *
from ..detection.oxygenator_detector import OxygenatorDetector
from ..segmentation.segmentor import Segmentor, ThrombusType
from ..models import (
    Ecmo,
    Image as EcmoImage,
    AnnotationSession,
    Segmentation,
    PromptType,
    Point,
)
from .. import db
from ..helpers import decode_img, decode_mask, encode_img, encode_mask


def create_image(ecmo: Ecmo, image_file: FileStorage):
    original_img = np.array(Image.open(image_file.stream), dtype=np.uint8)

    cropped, mm2_per_pixel = OxygenatorDetector(original_img, ecmo.type).detect_oxygenator()

    thumbnail, _ = resize_with_scaling_factor(cropped, 512)

    ecmo_image = EcmoImage(
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


def create_annotation_session(image: EcmoImage) -> None:
    mask = np.zeros((image.width_cropped, image.height_cropped), dtype=np.bool)
    annotation_session = AnnotationSession(image_id=image.id, mask=encode_mask(mask))
    db.session.add(annotation_session)


def create_segmentation(
    ecmo_image: EcmoImage,
    annotation_session: AnnotationSession,
    path: list[Point],
    thrombus_type: ThrombusType,
) -> bytes:
    img = decode_img(ecmo_image.cropped)
    session_mask = decode_mask(annotation_session.mask)

    segmentor = Segmentor(img, session_mask)
    thrombus_mask = segmentor.segment(path, thrombus_type)
    area = int(np.count_nonzero(thrombus_mask))

    annotation_session.mask = encode_mask(segmentor.img_mask)
    annotation_session.area += area

    segmentation = Segmentation(
        annotation_session_id=annotation_session.id,
        prompt_type=PromptType.POINT if len(path) == 1 else PromptType.CIRCLE,
        thrombus_type=thrombus_type,
        path=path,
        mask=encode_mask(thrombus_mask),
        area=area,
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
