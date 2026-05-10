import numpy as np
from typing import Sequence
import cv2 as cv
import json
import math
from PIL import Image, ImageFile
from uuid import UUID, uuid4
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from skimage.morphology import skeletonize

from .utils.img_utils import *
from .detection.oxygenator_detector import OxygenatorDetector, OxygenatorType
from .segmentation.segmentor import Segmentor
from .models import Image as EcmoImage
# from .RANSAC.RANSAC import (
#     LinearRANSAC,
#     default_criterion,
# )
# from .hough.hough import Hough
# from .clustering.clustering import AgglomerativeClustering
# from .fitting_objects.linear_equation import LinearEquation

def create_image(image_file: FileStorage):
    filename = f"{uuid4().hex}_{secure_filename(image_file.filename)}"
    image = Image.open(image_file.stream)
    
    cropped = OxygenatorDetector(image, OxygenatorType.GETINGE).detect_oxygenator()

    square_pixels_area = cropped.shape[0] * cropped.shape[1]
    square_mm_area = GETINGE_ECMO_SIDE_LENGTH_MM**2
    mm2_per_p2 = square_mm_area / square_pixels_area

    image = EcmoImage(
        ecmo_id=ecmo_id,
        filename=filename,
        original_data=image_file.read(),
        cropped_data=cropped.tobytes(),
        width_px=image_data.width,
        height_px=image_data.height,
        mm2_per_p2=mm2_per_p2,
    )
    db.session.add(image)
    db.session.commit()

    image_data.close()
    image_file.close()

    img = Image.fromarray(cropped)
    file_object = io.BytesIO()
    img.save(file_object, "jpeg")
    file_object.seek(0)

# def crop_circular_oxygenator(img_path: str) -> np.ndarray:
#     original_img = np.asarray(Image.open(img_path))
#     img, scaling_factor = resize_with_scaling_factor(original_img, 512)
#     greyscale = make_greyscale(img, [0, 0.5, 0.5])
#     edges = cv.Canny(greyscale, 300, 500)

#     fits = CircularRANSAC(edges, verbose=True, every=1000).fit(
#         3,
#         6000,
#         threshold=1,
#         num_inliers=240,
#         criterion=circular_criterion,
#         hook=eliminate_similar_by_inliers,
#     )
#     smallest = sorted(fits, key=lambda x: x[0].radius)[0]

#     smallest = rescale_circle(smallest[0], scaling_factor)

#     mask = mask_circle(smallest, original_img)
#     img = original_img.copy()
#     img[mask == 0] = np.array([255, 255, 255])
#     img, mask = paired_crop(img, mask, smallest, 30)

#     return img

def segment_image(image: EcmoImage, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    image_data = np.frombuffer(image.cropped_data, dtype=np.uint8).reshape(image.width_px, image.height_px)
    
    segmentor = Segmentor(image_data, image.current_mask)
    segmentor.segment(x1, y1, x2, y2, 4)

    return segmentor.mask
