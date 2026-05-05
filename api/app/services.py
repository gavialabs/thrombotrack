import numpy as np
from typing import Sequence
import cv2 as cv
import json
import math
from PIL import ImageFile

import matplotlib.pyplot as plt

from PIL import Image
from sklearn.cluster import KMeans
from skimage.morphology import skeletonize

from .img_utils import *
from .detection.linear_equation import LinearEquation
# from .RANSAC.RANSAC import (
#     LinearRANSAC,
#     default_criterion,
# )
# from .hough.hough import Hough
# from .clustering.clustering import AgglomerativeClustering
# from .fitting_objects.linear_equation import LinearEquation


def crop_diamond_oxygenator(image_file: ImageFile) -> np.ndarray:
    # original_img = np.array(Image.open(img_path))
    original_img = np.array(image_file)
    img, scaling_factor = resize_with_scaling_factor(original_img, 1024)

    img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
    img = cv.normalize(img, None, alpha=0, beta=255, norm_type=cv.NORM_MINMAX)
    img = cv.GaussianBlur(img, (5, 5), cv.BORDER_DEFAULT)

    ret, _ = cv.threshold(img, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

    edges = cv.Canny(img, ret / 3 * 2, ret * 2)

    rho = 1  # distance resolution in pixels of the Hough grid
    theta = np.pi / 180  # angular resolution in radians of the Hough grid
    threshold = 150  # minimum number of votes (intersections in Hough grid cell)
    min_line_length = 30  # minimum number of pixels making up a line
    max_line_gap = 0  # maximum gap in pixels between connectable line segments
    line_image = np.copy(img) * 0  # creating a blank to draw lines on

    lines = cv.HoughLinesP(
        edges,
        rho,
        theta,
        threshold,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap,
    )

    linear_equations = []

    for line in lines:
        for x1, y1, x2, y2 in line:
            linear_equations.append(LinearEquation.from_points((x1, y1), (x2, y2)))
            cv.line(line_image, (x1, y1), (x2, y2), (255, 0, 0), 3)

    intersections = np.asarray(
        find_pos_neg_intersections_in_image(linear_equations, img.shape)
    )

    h, w = img.shape[:2]
    kmeans = KMeans(
        n_clusters=4, init=[[0, h / 2], [w / 2, 0], [w, h / 2], [w / 2, h]]
    ).fit(intersections)

    assignments = kmeans.labels_
    centers = kmeans.cluster_centers_

    left_cluster = intersections[assignments == np.argmin(centers[:, 0])]
    right_cluster = intersections[assignments == np.argmax(centers[:, 0])]
    top_cluster = intersections[assignments == np.argmin(centers[:, 1])]
    bottom_cluster = intersections[assignments == np.argmax(centers[:, 1])]

    left_center = np.mean(left_cluster, axis=0)
    right_center = np.mean(right_cluster, axis=0)
    top_center = np.mean(top_cluster, axis=0)
    bottom_center = np.mean(bottom_cluster, axis=0)

    expected_side_length = np.linalg.norm(
        [
            left_center - top_center,
            top_center - right_center,
            right_center - bottom_center,
            bottom_center - left_center,
        ],
        axis=1,
    ).mean()

    left_cluster = remove_outliers(
        left_cluster, [top_center, bottom_center], expected_side_length
    )
    right_cluster = remove_outliers(
        right_cluster, [top_center, bottom_center], expected_side_length
    )
    top_cluster = remove_outliers(
        top_cluster, [left_center, right_center], expected_side_length
    )
    bottom_cluster = remove_outliers(
        bottom_cluster, [left_center, right_center], expected_side_length
    )

    leftmost = max(left_cluster, key=lambda x: x[0])
    rightmost = min(right_cluster, key=lambda x: x[0])
    uppermost = max(top_cluster, key=lambda x: x[1])
    lowermost = min(bottom_cluster, key=lambda x: x[1])

    corners = np.array([leftmost, uppermost, rightmost, lowermost], dtype=np.float32)
    rescaled_corners = np.array(
        rescale_points(corners, scaling_factor), dtype=np.float32
    )

    side_length = int(
        np.mean(
            [
                np.linalg.norm(rescaled_corners[1] - rescaled_corners[0]),
                np.linalg.norm(rescaled_corners[2] - rescaled_corners[1]),
                np.linalg.norm(rescaled_corners[3] - rescaled_corners[2]),
                np.linalg.norm(rescaled_corners[0] - rescaled_corners[3]),
            ]
        )
    )

    corners = rescaled_corners
    output_points = np.float32(
        [[0, 0], [0, side_length], [side_length, 0], [side_length, side_length]]
    )
    M = cv.getPerspectiveTransform(
        np.array([corners[1], corners[0], corners[2], corners[3]], dtype=np.float32),
        output_points,
    )
    dst = cv.warpPerspective(original_img, M, (side_length, side_length))

    # border = int(0.1 * side_length)
    # dst = dst[border:side_length - border,border:side_length - border]

    return dst

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
