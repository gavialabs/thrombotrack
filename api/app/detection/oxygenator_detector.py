"""Module for automatically cropping images of oxygenators."""

import cv2
import math
import numpy as np
from sklearn.cluster import KMeans
from typing import Sequence

from app.constants import *
from app.detection.linear_equation import LinearEquation
from app.detection.RANSAC import Circle, CircularRANSAC, CircularRANSACFit
from app.helpers import resize_with_scaling_factor, make_greyscale


def find_pos_neg_intersections_in_image(
    lines: list[LinearEquation], img_shape: tuple[int, int]
) -> list[tuple[float, float | None]]:
    """Finds intersections of roughly perpendicular lines.

    Finds the intersections of given lines that occur within the bounds of an image,
    but only if the lines are roughly perpendicular (within 25% of the value of the slope).

    Args:
        lines: List of LinearEquations.
        img_shape: Shape of the image the lines were detected in.

    Returns:
        List of intersection coordinates.
    """

    def in_image(point: tuple[float, float | None]) -> bool:
        x, y = point

        if y is None:
            return x > 0 and x < img_shape[1]

        return (x > 0 and x < img_shape[1]) and (y > 0 and y < img_shape[0])

    def opposite_slopes(l1: LinearEquation, l2: LinearEquation) -> bool:
        if l1.slope is None:
            return l2.slope == 0

        if l2.slope is None:
            return l1.slope == 0

        s1 = l1.slope < 0
        s2 = l2.slope < 0

        if s1 == s2:
            return False

        return math.isclose(l1.slope, -1 / l2.slope, rel_tol=0.25)

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


def rescale_points(points: np.ndarray, scaling_factor: float) -> list[list[int]]:
    """Rescales a set of points to coincide with the scaling of an image.

    Args:
        points: List of points.
        scaling_factor: Scaling factor to multiply by.

    Returns:
        Rescaled version of the points.
    """
    rescaled = (np.array(points) * (1 / scaling_factor)).tolist()
    out = [[round(p, 0) for p in point] for point in rescaled]
    return out


class OxygenatorDetector:
    """Detects oxygenators in images.

    Attributes:
        original_image: Original image array uploaded by user containing an oxygenator.
        oxygenator_type: Type of oxygenator in image (HLS/Nautilus)
        img: Rescaled and grayscaled image array.
        scaling_factor: Factor by which the original image was rescaled.
    """

    def __init__(self, original_img: np.ndarray, oxygenator_type: OxygenatorType):
        """Initializes with an original image and oxygenator type and performs preprocessing."""
        self.original_img = original_img
        self.oxygenator_type = oxygenator_type

        self.preprocess()

    def preprocess(self) -> None:
        """Rescales and grayscales original image."""
        if self.oxygenator_type == OxygenatorType.HLS:
            img, scaling_factor = resize_with_scaling_factor(
                self.original_img, HLS_LONGEST_SIDE
            )
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)  # type: ignore
            img = cv2.normalize(img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)  # type: ignore
            img = cv2.GaussianBlur(img, (HLS_GAUSSIAN_BLUR, HLS_GAUSSIAN_BLUR), cv2.BORDER_DEFAULT)  # type: ignore
        else:
            img, scaling_factor = resize_with_scaling_factor(
                self.original_img, NAUTILUS_LONGEST_SIDE
            )
            img = make_greyscale(img, NAUTILUS_GRAYSCALE_WEIGHTS)

        self.img: np.ndarray = img  # type: ignore
        self.scaling_factor = scaling_factor

    def detect_oxygenator(self) -> tuple[np.ndarray, float]:
        """Detects an oxygenator in original image and crops to the detected area.

        Uses the length of the detected image to determine a conversion factor between square
        millimeters and pixels for this image.

        Returns:
            Cropped image array and conversion factor.
        """
        if self.oxygenator_type == OxygenatorType.HLS:
            lines = self.find_lines()
            corners = self.find_corners(lines)
            warped = self.warp_perspective(corners)

            area_pixels = warped.shape[0] * warped.shape[1]
            area_mm2 = HLS_SIDE_LENGTH_MM**2.0
        else:
            circle = self.find_circle()
            warped = self.crop_to_circle(circle)

            area_pixels = np.pi * ((warped.shape[0] / 2) ** 2)
            area_mm2 = np.pi * ((NAUTILUS_DIAMETER_MM / 2) ** 2)

        mm2_per_pixel = area_mm2 / area_pixels

        return warped, mm2_per_pixel

    def find_lines(self) -> list[LinearEquation]:
        """Detects lines within image using probabilistic Hough algorithm."""
        ret, _ = cv2.threshold(self.img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        edges = cv2.Canny(self.img, ret / 3 * 2, ret * 2)

        lines = cv2.HoughLinesP(
            edges,
            HOUGH_RHO,
            HOUGH_THETA,
            HOUGH_THRESHOLD,
            minLineLength=HOUGH_MIN_LINE_LENGTH,
            maxLineGap=HOUGH_MAX_LINE_GAP,
        )

        linear_equations = []

        for line in lines:
            for x1, y1, x2, y2 in line:
                linear_equations.append(LinearEquation.from_points((x1, y1), (x2, y2)))

        return linear_equations

    def find_corners(self, lines: list[LinearEquation]) -> np.ndarray:
        """Detects corners of a square described by list of lines.

        Finds roughly perpendicular interesections between given lines. Uses k-means clustering to
        group intersections into 4 groups. Finds expected side length as mean distance between
        clusters and uses this to remove outlier points. Takes the innermost remaining points and
        rescales to original image dimensions.

        Args:
            lines: List of LinearEquations.

        Returns:
            Array of left, top, right, and bottom corner coordinates in original image dimensions.
        """

        def remove_outliers(
            points: np.ndarray,
            neighbors: Sequence[np.ndarray],
            expected_dist: float,
            tol: float = CORNER_OUTLIER_TOL,
        ) -> np.ndarray:
            """Filters outlier points whose distance to adjacent square corners is greater than a
            tolerance."""
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
        """Transforms the list of corners on an image to a perfect square."""
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

    def crop_to_circle(
        self, circle: Circle, buffer: int = CIRCLE_CROP_BUFFER
    ) -> np.ndarray:
        """Crops the original image to the edges of the given circle with an optional buffer."""
        cx, cy = circle.center
        r = circle.radius + buffer
        return self.original_img[cy - r : cy + r + 1, cx - r : cx + r + 1]

    def find_circle(self) -> Circle:
        """Detects a circle in image using Canny and RANSAC."""

        def rescale_circle(circle: Circle, scaling_factor: float) -> Circle:
            """Rescales a circle equation by a given scaling factor."""
            cx, cy = circle.center
            r = circle.radius
            new_center = rescale_points(np.array([cx, cy]), scaling_factor)[0]
            cx, cy = new_center
            r = 1 / scaling_factor * r
            conv = lambda x: int(round(x, 0))
            return CircularRANSACFit((conv(cx), conv(cy)), conv(r))

        edges = cv2.Canny(self.img, CIRCLE_CANNY_THRESH1, CIRCLE_CANNY_THRESH2)
        fits = CircularRANSAC(edges).fit(
            RANSAC_NUM_POINTS,
            RANSAC_NUM_SAMPLES,
            threshold=RANSAC_THRESHOLD,
            num_inliers=RANSAC_NUM_INLIERS,
        )
        sorted_fits = sorted(fits, key=lambda x: x[0].radius)[0]
        smallest = rescale_circle(sorted_fits[0], self.scaling_factor)

        return smallest
