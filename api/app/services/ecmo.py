import io
import numpy as np
from typing import Sequence
import cv2 as cv
import json
import math
from flask import current_app as app
from PIL import Image, ImageFile
from uuid import UUID, uuid4
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from skimage.morphology import skeletonize

from ..utils.img_utils import *
from ..detection.oxygenator_detector import OxygenatorDetector, OxygenatorType
from ..segmentation.segmentor import Segmentor, ThrombusType
from ..models import (
    Image as EcmoImage,
    AnnotationSession,
    Segmentation,
    PromptType,
)
from .. import db

# from .RANSAC.RANSAC import (
#     LinearRANSAC,
#     default_criterion,
# )
# from .hough.hough import Hough
# from .clustering.clustering import AgglomerativeClustering
# from .fitting_objects.linear_equation import LinearEquation


def create_image(ecmo_id: UUID, image_file: FileStorage):
    image = Image.open(image_file.stream)

    cropped_image, mm2_per_pixel = OxygenatorDetector(
        image, OxygenatorType.GETINGE
    ).detect_oxygenator()

    cropped_image_file = io.BytesIO()
    cropped_image.save(cropped_image_file, "jpeg")
    cropped_image_file.seek(0)

    cropped_image_data = cropped_image_file.read()

    ecmo_image = EcmoImage(
        ecmo_id=ecmo_id,
        filename=f"{uuid4().hex}_{secure_filename(image_file.filename)}",
        mimetype=image_file.mimetype,
        original=image_file.read(),
        cropped=cropped_image_data,
        width_original=image.width,
        height_original=image.height,
        width_cropped=cropped_image.width,
        height_cropped=cropped_image.height,
        mm2_per_pixel=mm2_per_pixel,
    )
    db.session.add(ecmo_image)
    db.session.flush()

    create_annotation_session(ecmo_image)

    db.session.commit()

    image.close()
    cropped_image.close()
    image_file.close()
    cropped_image_file.close()

    return ecmo_image


def create_annotation_session(image: EcmoImage) -> None:
    mask = np.zeros((image.width_cropped, image.height_cropped), dtype=np.bool)

    mask_file = io.BytesIO()
    Image.fromarray(mask).save(mask_file, "jpeg")
    mask_file.seek(0)

    annotation_session = AnnotationSession(
        image_id=image.id,
        mask=mask_file.read()
    )
    db.session.add(annotation_session)


def create_segmentation(
    ecmo_image: EcmoImage,
    annotation_session: AnnotationSession,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
) -> None:
    image = np.asarray(Image.open(io.BytesIO(ecmo_image.cropped)))
    session_mask = np.array(Image.open(io.BytesIO(annotation_session.mask)), dtype=np.bool)

    segmentor = Segmentor(image, session_mask)
    thrombus_mask = segmentor.segment(x1, y1, x2, y2, ThrombusType.CLOT)

    thrombus_mask_file = io.BytesIO()
    Image.fromarray(thrombus_mask).save(thrombus_mask_file, "jpeg")
    thrombus_mask_file.seek(0)
    
    session_mask_file = io.BytesIO()
    Image.fromarray(segmentor.mask).save(session_mask_file, "jpeg")
    session_mask_file.seek(0)

    annotation_session.mask = session_mask_file.read()

    segmentation = Segmentation(
        annotation_session_id=annotation_session.id,
        prompt_type=PromptType.CIRCLE,
        thrombus_type=ThrombusType.CLOT,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        mask=thrombus_mask_file.read(),
        area=int(np.count_nonzero(thrombus_mask)),
    )
    db.session.add(segmentation)
    db.session.commit()
