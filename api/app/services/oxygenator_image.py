"""Services for interacting with OxygenatorImages in the database."""

import numpy as np
from PIL import Image
from sqlalchemy import func
from uuid import UUID
from werkzeug.datastructures import FileStorage

from .. import db
from app.constants import OxygenatorType, NAUTILUS_DIAMETER_MM, HLS_SIDE_LENGTH_MM
from app.detection.oxygenator_detector import (
    OxygenatorDetector,
    warp_perspective,
    crop_to_circle,
)
from app.detection.RANSAC import Circle
from app.helpers import encode_img, resize_with_scaling_factor, decode_img
from app.models import (
    Oxygenator,
    OxygenatorImage,
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
        .where(
            OxygenatorImage.oxygenator_id == oxygenator_id,
            OxygenatorImage.cropped != None,
        )
        .order_by(OxygenatorImage.created_at)
    )

    return db.session.execute(stmt)


def create_image(
    oxygenator: Oxygenator, image_file: FileStorage
) -> tuple[OxygenatorImage, UUID | None]:
    """Crops an oxygenator image and starts an annotation session.

    Uses OxygenatorDetector to crop image and calculate conversion factor. Creates a thumbnail.
    Starts an annotation session if cropping was successful (otherwise returns None for annotation
    session ID so that the user can manually crop the image first).

    Args:
        oxygenator: Oxygenator to create the image for.
        image_file: File containing image of oxygenator.

    Returns:
        New OxygenatorImage object and ID of new AnnotationSession.
    """
    original_img = np.array(Image.open(image_file.stream), dtype=np.uint8)

    img, mm2_per_pixel = OxygenatorDetector(
        original_img, oxygenator.type
    ).detect_oxygenator()
    did_crop = mm2_per_pixel is not None

    thumbnail = None
    if did_crop:
        thumbnail, _ = resize_with_scaling_factor(img, 512)
        thumbnail = encode_img(thumbnail)

    oxygenator_image = OxygenatorImage(
        oxygenator_id=oxygenator.id,
        original=encode_img(original_img),
        thumbnail=thumbnail,
        cropped=encode_img(img) if did_crop else None,
        height_original=original_img.shape[0],
        width_original=original_img.shape[1],
        height_cropped=img.shape[0] if did_crop else None,
        width_cropped=img.shape[1] if did_crop else None,
        mm2_per_pixel=mm2_per_pixel,
    )
    db.session.add(oxygenator_image)
    db.session.flush()

    if did_crop:
        annotation_session = create_annotation_session(oxygenator_image)

    db.session.commit()

    image_file.close()

    return oxygenator_image, annotation_session.id if did_crop else None


def manual_crop_image(
    oxygenator_image: OxygenatorImage,
    oxygenator_type: OxygenatorType,
    origin_x: float,
    origin_y: float,
    scale: float,
) -> tuple[OxygenatorImage, UUID | None]:
    """Crops an oxygenator image based on user input and starts an annotation session.

    After the user has panned/zoomed the image to fit within the cropping shape, undoes their
    transformations and crops the image to the shape. Calculates a conversion factor based on the
    oxygenator type and the cropped image size. Sets the cropped data and new thumbnail and starts
    an annotation session.
    
    Args:
        oxygenator_image: OxygenatorImage to crop.
        oxygenator_type: Type of oxygenator to crop.
        origin_x: x-coordinate of the image offset to fit in cropping shape.
        origin_y: y-coordinate of the image offset to fit in cropping shape.
        scale: Scale factor of the image (1 = no scaling, 0.5 = half size, 2 = double size, etc.).

    Returns:
        New OxygenatorImage object and ID of new AnnotationSession.
    """
    original_img = decode_img(oxygenator_image.original)
    h, w = original_img.shape[:2]

    # diagonal and diameter are set to 3/4 of the image width
    # if you want to make the cropping square/circle bigger, update this value here and in
    # AnnotateCanvas
    d = w * 3 / 4
    mid_height = h / 2
    mid_width = w / 2

    if oxygenator_type == OxygenatorType.HLS:
        left = (mid_height, mid_width - d / 2)
        top = (mid_height - d / 2, mid_width)
        right = (mid_height, mid_width + d / 2)
        bottom = (mid_height + d / 2, mid_width)

        coords = np.array([left, top, right, bottom])

        coords *= 1 / scale
        coords[:, 0] -= origin_y
        coords[:, 1] -= origin_x

        corners = np.array(
            [
                np.flip(coords[0]),
                np.flip(coords[1]),
                np.flip(coords[2]),
                np.flip(coords[3]),
            ],
            dtype=np.float32,
        )

        # currently this just crops and rotates to the selected region, but could use a corner-based
        # cropping instead if we want to retain perspective correction without auto-cropping
        cropped = warp_perspective(original_img, corners)

        area_pixels = cropped.shape[0] * cropped.shape[1]
        area_mm2 = HLS_SIDE_LENGTH_MM**2.0
    else:
        cx = mid_width
        cy = mid_height

        d *= 1 / scale
        cx *= 1 / scale
        cy *= 1 / scale
        cx -= origin_x
        cy -= origin_y

        circle = Circle((cx, cy), d / 2)
        cropped = crop_to_circle(original_img, circle)

        area_pixels = np.pi * ((cropped.shape[0] / 2) ** 2)
        area_mm2 = np.pi * ((NAUTILUS_DIAMETER_MM / 2) ** 2)

    thumbnail, _ = resize_with_scaling_factor(cropped, 512)

    oxygenator_image.cropped = encode_img(cropped)
    oxygenator_image.thumbnail = encode_img(thumbnail)
    oxygenator_image.height_cropped = cropped.shape[0]
    oxygenator_image.width_cropped = cropped.shape[1]
    oxygenator_image.mm2_per_pixel = area_mm2 / area_pixels

    annotation_session = create_annotation_session(oxygenator_image)

    db.session.commit()

    return oxygenator_image, annotation_session.id
