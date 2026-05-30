from flask import current_app as app
import cv2
import math
import numpy as np
from enum import Enum
from PIL import Image
from sklearn.cluster import KMeans
from typing import Sequence

from .linear_equation import LinearEquation
from .RANSAC import CircularRANSAC, CircularRANSACFit
from ..utils.img_utils import resize_with_scaling_factor, make_greyscale
from ..models import EcmoType

GETINGE_ECMO_SIDE_LENGTH_MM = 88
NAUTILUS_DIAMETER_MM = 87.5


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


class OxygenatorDetector:
    def __init__(self, original_img: np.ndarray, oxygenator_type: EcmoType) -> None:
        self.original_img = original_img
        self.oxygenator_type = oxygenator_type

        self.preprocess()

    def preprocess(self) -> None:
        if self.oxygenator_type == EcmoType.GETINGE:
            img, scaling_factor = resize_with_scaling_factor(self.original_img, 1024)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            img = cv2.normalize(img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
            img = cv2.GaussianBlur(img, (5, 5), cv2.BORDER_DEFAULT)
        else:
            img, scaling_factor = resize_with_scaling_factor(self.original_img, 512)
            img = make_greyscale(img, [0, 0.5, 0.5])

        self.img = img
        self.scaling_factor = scaling_factor

    def find_lines(self) -> list[LinearEquation]:
        ret, _ = cv2.threshold(self.img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        edges = cv2.Canny(self.img, ret / 3 * 2, ret * 2)

        rho = 1  # distance resolution in pixels of the Hough grid
        theta = np.pi / 180  # angular resolution in radians of the Hough grid
        threshold = 150  # minimum number of votes (intersections in Hough grid cell)
        min_line_length = 30  # minimum number of pixels making up a line
        max_line_gap = 0  # maximum gap in pixels between connectable line segments

        lines = cv2.HoughLinesP(
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

        return linear_equations

    def find_corners(self, lines: list[LinearEquation]) -> np.ndarray:
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

        candidates = np.asarray(
            find_pos_neg_intersections_in_image(lines, self.img.shape)
        )

        # cluster the candidate corners into four groups at left, top, right, and bottom of image
        h, w = self.img.shape[:2]
        kmeans = KMeans(
            n_clusters=4, init=[[0, h / 2], [w / 2, 0], [w, h / 2], [w / 2, h]]
        ).fit(candidates)

        assignments = kmeans.labels_
        centers = kmeans.cluster_centers_

        left_cluster = candidates[assignments == np.argmin(centers[:, 0])]
        top_cluster = candidates[assignments == np.argmin(centers[:, 1])]
        right_cluster = candidates[assignments == np.argmax(centers[:, 0])]
        bottom_cluster = candidates[assignments == np.argmax(centers[:, 1])]

        left_center = left_cluster.mean(axis=0)
        top_center = top_cluster.mean(axis=0)
        right_center = right_cluster.mean(axis=0)
        bottom_center = bottom_cluster.mean(axis=0)

        # calculate the average distance between the cluster centers
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

        # take the innermost points of each cluster as the final corners
        left = max(left_cluster, key=lambda x: x[0])
        top = max(top_cluster, key=lambda x: x[1])
        right = min(right_cluster, key=lambda x: x[0])
        bottom = min(bottom_cluster, key=lambda x: x[1])

        corners = np.array([left, top, right, bottom], dtype=np.float32)
        rescaled_corners = np.array(
            rescale_points(corners, self.scaling_factor), dtype=np.float32
        )

        return rescaled_corners

    def warp_perspective(self, corners: np.ndarray) -> np.ndarray:
        # calculate side length of resulting square as mean of difference between adjacent corners
        side_length = int(
            np.mean(
                [
                    np.linalg.norm(corners[1] - corners[0]),
                    np.linalg.norm(corners[2] - corners[1]),
                    np.linalg.norm(corners[3] - corners[2]),
                    np.linalg.norm(corners[0] - corners[3]),
                ]
            )
        )
        # maps the top corner to (0, 0) (basically rotates oxygenator by -45 degrees)
        output_points = np.array(
            [[0, side_length], [0, 0], [side_length, 0], [side_length, side_length]],
            dtype=np.float32,
        )
        M = cv2.getPerspectiveTransform(
            corners,
            output_points,
        )
        return cv2.warpPerspective(self.original_img, M, (side_length, side_length))

    def find_circle(self) -> np.ndarray:
        def rescale_circle(circle, scaling_factor):
            cx, cy = circle.center
            r = circle.radius
            new_center = rescale_points([[cx, cy]], scaling_factor)[0]
            cx, cy = new_center
            r = 1 / scaling_factor * r
            conv = lambda x: int(round(x, 0))
            return CircularRANSACFit((conv(cx), conv(cy)), conv(r))

        def crop_to_circle(img, circle, buffer):
            cx, cy = circle.center
            r = circle.radius + buffer
            img = img[cy - r : cy + r + 1, cx - r : cx + r + 1]
            return img

        edges = cv2.Canny(self.img, 300, 500)
        fits = CircularRANSAC(edges).fit(
            3,
            6000,
            threshold=1,
            num_inliers=240,
        )
        smallest = sorted(fits, key=lambda x: x[0].radius)[0]
        smallest = rescale_circle(smallest[0], self.scaling_factor)

        return crop_to_circle(self.original_img, smallest, 0)

    def detect_oxygenator(self) -> tuple[np.ndarray, float]:
        if self.oxygenator_type == EcmoType.GETINGE:
            lines = self.find_lines()
            corners = self.find_corners(lines)
            warped = self.warp_perspective(corners)

            area_pixels = warped.shape[0] * warped.shape[1]
            area_mm2 = GETINGE_ECMO_SIDE_LENGTH_MM**2.0
        else:
            warped = self.find_circle()

            area_pixels = np.pi * ((warped.shape[0] / 2) ** 2)
            area_mm2 = np.pi * ((NAUTILUS_DIAMETER_MM / 2) ** 2)

        mm2_per_pixel = area_mm2 / area_pixels

        return warped, mm2_per_pixel
