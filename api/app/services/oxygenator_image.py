# Oxygenator image services

import numpy as np
from PIL import Image
from sqlalchemy import func
from uuid import UUID
from werkzeug.datastructures import FileStorage

from app.helpers import resize_with_scaling_factor
from app.detection.oxygenator_detector import OxygenatorDetector
from app.models import (
    Oxygenator,
    OxygenatorImage,
)
from .. import db
from app.helpers import (
    encode_img,
)
from app.services.annotation_session import create_annotation_session


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
