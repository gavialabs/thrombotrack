"""Module for performing RANSAC to detect a circle in an image."""

import math
import numpy as np
import random
from typing import Callable, Sequence

from app.detection.linear_equation import LinearEquation

try:
    from typing import Self
except:
    from typing_extensions import Self

Point = tuple[float, float]


def find_center(p1: Point, p2: Point, p3: Point) -> Point | None:
    """Finds center of circle given three points."""

    def midpoint(p1: Point, p2: Point) -> Point:
        """Finds midpoint of two points."""
        x1, y1 = p1
        x2, y2 = p2

        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        return (mx, my)

    l1 = LinearEquation.from_points(p1, p2)
    l2 = LinearEquation.from_points(p2, p3)

    if l1 == l2:
        return None

    m1 = midpoint(p1, p2)
    m2 = midpoint(p2, p3)

    l3 = l1.from_slope_point(l1.perpendicular_slope(), m1)
    l4 = l2.from_slope_point(l2.perpendicular_slope(), m2)

    return l3.intersection(l4)  # type: ignore


class Circle:
    """Describes a circle.

    Attributes:
        center: Center of the circle.
        radius: Radius of the circle.
    """

    def __init__(self, center: Point, radius: float):
        """Initializes with a given center and radius."""
        self.center = center
        self.radius = radius

    @classmethod
    def from_sample(cls, arr: Sequence | np.ndarray) -> Self:
        """Initializes from a sample of three points."""
        if not isinstance(arr, np.ndarray):
            try:
                arr = np.array(arr)
            except TypeError as e:
                print(
                    "Expected to be able to convert arr to a "
                    f"numpy array, instead got: {e}"
                )
                raise
        assert arr.shape[1] == 2, (
            "Points must be 2-dimensional, "
            f"but got {arr.shape[0]} for point dimension."
        )
        assert arr.shape[0] >= 3, "Must provide at least 3 points to fit a circle."
        assert np.unique(arr, axis=0).shape[0] >= 3, (
            "Must provide at least 3 unique "
            "points to fit a circle. Your dataset included duplicated points."
        )

        x, y = arr[:, 0], arr[:, 1]
        A = np.vstack([2 * x, 2 * y, np.ones(len(x))]).T
        v = x**2 + y**2

        cx, cy, c3 = np.linalg.lstsq(A.T @ A, A.T @ v, rcond=None)[0]

        r = np.sqrt(c3 + cx**2 + cy**2)

        return cls((float(cx), float(cy)), float(r))


class CircularRANSACFit(Circle):
    """Describes a RANSAC fit of a circle.

    Attributes:
        center: Center of the circle.
        radius: Radius of the circle.
    """

    min_num_points = 3

    def __init__(self, center: Point, radius: float):
        """Initializes using center and radius."""
        super().__init__(center, radius)

    @classmethod
    def fit(cls, arr: Sequence | np.ndarray) -> Self:
        """Initializes from a list of points."""
        return cls.from_sample(arr)

    def inliers(self, points: np.ndarray, threshold: int):
        """Finds inliers with a given threshold."""
        cx, cy = self.center
        r = self.radius
        dists = points - np.array([cx, cy])
        dists = np.sqrt(np.sum(dists**2, axis=-1))
        inlier_args = np.argwhere((dists > (r - threshold)) & (dists < (r + threshold)))
        return points[inlier_args, :].squeeze()


class Sampler:
    """Iterable across a number of samples.

    Attributes:
        points: Array of points.
        num_points: Number of points to fit.
        num_samples: Number of samples to take.
        data_size: Number of points given.
        sampled_set: List of sampled indices.
    """

    def __init__(self, points: np.ndarray, num_points: int, num_samples: int):
        """Initializes with an array of points, number of points to fit, and number of samples to
        take."""
        if not isinstance(points, np.ndarray):
            try:
                points = np.array(points)
            except TypeError as e:
                print(
                    "Expected to be able to convert points to a "
                    f"numpy array, instead got: {e}"
                )
        self.points = points
        self.num_points = num_points
        self.num_samples = num_samples
        self.data_size = self.points.shape[0]

        self.num_samples = min(
            math.comb(self.data_size, self.num_points), self.num_samples
        )

        # Ensure unique samples
        sample: set[tuple[int, ...]] = set()
        while len(sample) < self.num_samples:
            indexes = tuple(
                sorted(random.sample(range(self.data_size), self.num_points))
            )
            sample.add(indexes)

        self.sampled_set = [list(item) for item in list(sample)]

    def __len__(self):
        return len(self.sampled_set)

    def __getitem__(self, ind):
        return np.array(self.points[self.sampled_set[ind], :])


Fit = tuple[CircularRANSACFit, np.ndarray]


def criterion(
    fits: list[Fit],
    points: np.ndarray,
    threshold: int,
    num_inliers: int,
    num_objects: int | None = None,
) -> list[Fit]:
    """Criterion for picking which fitted objects to accept from the RANSAC fit.

    Args:
        fits: List of tuples which contain the fitted object and its inliers.
        points: Complete set of points on which RANSAC is being fit.
        threshold: Threshold around which to consider points as being inliers.
        num_inliers: Number of inliers to consider being a real object.
        num_objects: Hard maximum of the number of objects to keep (or 1).

    Returns:
        List of tuples which contain the fitted object and its inliers.
    """

    # The last fit in the list is the most recent.
    prev_fit = fits.pop(-1)
    prev_inliers = prev_fit[1]

    # note: not sure if this is a good idea
    if len(prev_inliers) < CircularRANSACFit.min_num_points:
        return [*fits, prev_fit]

    # Fit it again on the set of inliers until it stops improving the fit.
    fitted = CircularRANSACFit.fit(prev_inliers)
    inliers = fitted.inliers(points, threshold)
    while inliers.shape[0] > prev_inliers.shape[0]:
        prev_inliers = inliers
        fitted = CircularRANSACFit.fit(prev_inliers)
        inliers = fitted.inliers(points, threshold)

    # If the inlier set of the latest fit is too small, just return the
    # list without it.
    if inliers.shape[0] < num_inliers:
        return fits

    # Check that all of the fitted objects are unique.
    fits.append(tuple([fitted, inliers]))
    unique = set([item[0] for item in fits])
    new_fits = []
    for item in fits:
        fit = item[0]
        if fit in unique:
            new_fits.append(item)
            unique.remove(fit)

    # Return the top num_objects.
    fits = sorted(new_fits, key=lambda x: -x[1].shape[0])
    if num_objects is None:
        return fits

    return fits[:num_objects]


def eliminate_similar_by_inliers(
    fits: list[Fit], points: np.ndarray, shared_threshold: float = 0.1
) -> list[Fit]:
    """Eliminates circles found by RANSAC if they are fitting similar inlier sets."""

    def convert_to_index(inliers: np.ndarray, points: np.ndarray) -> np.ndarray:
        """Converts a list of points in an inlier array to indices."""
        indexes = []
        for point in inliers:
            indexes.append(np.where((points == point).all(axis=1))[0])
        return np.array(indexes)

    eliminate = []
    temp_fits = [[item[0], convert_to_index(item[1], points)] for item in fits]
    count = 1
    for i, fit1 in enumerate(temp_fits):
        inliers1: np.ndarray = fit1[1]  # type: ignore
        size1 = inliers1.size
        for j, fit2 in enumerate(temp_fits[i + 1 :]):
            inliers2: np.ndarray = fit2[1]  # type: ignore
            size2 = inliers2.size

            intersect = np.intersect1d(inliers1, inliers2, assume_unique=True)
            intersect_size = intersect.size
            if intersect_size >= (shared_threshold * size1) or intersect_size >= (
                shared_threshold * size2
            ):
                count += 1
                eliminate.append(i + 1 + j)

    eliminate = sorted(list(set(eliminate)), key=lambda x: -x)
    for i in eliminate:
        fits.pop(i)

    return fits


class CircularRANSAC:
    """Fits a circle using RANSAC.

    Attributes:
        points: Array of points to fit.
    """

    def __init__(self, points: Sequence | np.ndarray):
        """Initializes with an array of points."""

        def binary_array_to_xy(array):
            """
            Converts an array to a set of indexes where the array is > 0

            Args:
                array: the given array.

            Returns:
                a set of indexes.
            """
            ys, xs = np.where(array)
            return np.array([[x, y] for x, y in zip(xs, ys)])

        if not isinstance(points, np.ndarray):
            try:
                points = np.array(points)
            except TypeError as e:
                print(
                    "Expected to be able to convert points to a "
                    f"numpy array, instead got: {e}"
                )
        self.points = binary_array_to_xy(points)

    def fit(
        self,
        num_points: int,
        num_samples: int,
        threshold: int,
        num_inliers: int,
        criterion: Callable[[list[Fit], np.ndarray, int, int], list[Fit]] = criterion,
        hook: (
            Callable[[list[Fit], np.ndarray], list[Fit]] | None
        ) = eliminate_similar_by_inliers,
    ) -> list[Fit]:
        """Fits a circle using RANSAC.

        Args:
            num_points: Number of points to fit to. If this is less than the number of points
                required by the object, this number will be automatically set to that number.
            num_samples: How many samples to use.
            threshold: Threshold of the margin to search for inliers.
            num_inliers: Number of inliers required to consider the object to be a correct fit.
            criterion: Function that determines which fitted objects to accept.
            hook: Optional post-processing function to further refine the fits.

        Returns:
            List of tuples containing a fitted object found by RANSAC and its inlier set of points.
        """

        if num_points < CircularRANSACFit.min_num_points:
            num_points = CircularRANSACFit.min_num_points

        sampler = Sampler(self.points, num_points, num_samples)
        fits = []
        for _, point_set in enumerate(sampler):  # type: ignore
            fit_object = CircularRANSACFit.fit(point_set)
            inliers = fit_object.inliers(self.points, threshold)

            fits.append(tuple([fit_object, inliers]))
            fits = criterion(fits, self.points, threshold, num_inliers)

        if hook is not None:
            return hook(fits, self.points)

        return fits
