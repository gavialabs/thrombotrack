import numpy as np
import math
from PIL import Image
# import matplotlib.pyplot as plt
# import cv2 as cv
# import skimage as ski
# from shapely.geometry import MultiPolygon, Point, Polygon
from collections.abc import Sequence
# from skimage.morphology import dilation

def rescale(image, scaling_factor):
    """
    Rescales an image by a scaling factor.

    Args:
        image: either a PIL image or a numpy array to be resized.
        scaling_factor: float to resize the image dimensions by.

    Returns:
        image: rescaled image of the same type.
    """

    is_array = False
    if isinstance(image, np.ndarray):
        h, w = image.shape[:2]
        image = Image.fromarray(image)
        is_array = True
    else:
        w, h = image.size

    image = image.resize((int(w * scaling_factor), int(h * scaling_factor)))
    if is_array:
        image = np.asarray(image)
    return image


def resize_with_scaling_factor(image, longest_side):
    """
    Rescales an image by scaling its longest side to a given length.

    Args:
        image: either a PIL image or a numpy array to be resized.
        longest_side: int the new size of the image's longest side.

    Returns:
        image: resized image of the same type.
        scaling_factor: a factor by which the image is scaled, for reference.
    """
    if isinstance(image, np.ndarray):
        h, w = image.shape[:2]
    else:
        w, h = image.size

    curr_longest = max(h, w)
    scaling_factor = longest_side / curr_longest
    return rescale(image, scaling_factor), scaling_factor


def find_pos_neg_intersections_in_image(lines, img_shape):
    """
    Finds the intersections of given lines that occur within the bounds of an image,
    but only if the lines have opposite sign slopes.

    Args:
        lines: a list of LienarEquation objects.
        img_shape: the dimensions of an image the lines are derived from.

    Returns:
        intersections: a list of intersection points.
    """

    def in_image(point):
        x, y = point
        return (x > 0 and x < img_shape[1]) and (y > 0 and y < img_shape[0])

    def opposite_slopes(l1, l2):
        if l1.slope is None:
            return l2.slope == 0

        if l2.slope is None:
            return l1.slope == 0

        s1 = l1.slope < 0
        s2 = l2.slope < 0

        if s1 == s2:
            return False

        # if l2.slope == 0:
        #     return math.isclose(l1.slope, )

        return math.isclose(l1.slope, -1 / l2.slope, rel_tol=0.25)  # was at 0.2

    intersections = []
    for i, line1 in enumerate(lines):
        for line2 in lines[i + 1 :]:
            intersection = line1.intersection(line2)
            if intersection is None:
                pass
            elif not in_image(intersection):
                pass
            elif not opposite_slopes(line1, line2):
                pass
            else:
                intersections.append(intersection)

    return intersections


def remove_outliers(
    points: np.ndarray,
    neighbors: Sequence[np.ndarray],
    expected_dist: float,
    tol: float = 0.8,
):
    dist_to_neighbor_1 = np.linalg.norm(points - neighbors[0], axis=1)
    dist_to_neighbor_2 = np.linalg.norm(points - neighbors[1], axis=1)

    min_dists = np.min([dist_to_neighbor_1, dist_to_neighbor_2], axis=0)

    return points[min_dists >= tol * expected_dist]


def rescale_points(points, scaling_factor):
    """
    Rescales a set of points to coincide with the scaling of an image

    Args:
        points: a list of points.
        scaling_factor: a scaling factor to multiply by.

    Returns:
        out: a rescaled version of the points.
    """
    out = np.array(points) * (1 / scaling_factor)
    out = out.tolist()
    out = [[round(p, 0) for p in point] for point in out]
    return out