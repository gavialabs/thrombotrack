import numpy as np
import random
from math import *
from typing import Tuple
from .linear_equation import LinearEquation

try:
    from typing import Self
except:
    from typing_extensions import Self

def midpoint(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    mx = (x1 + x2)/2
    my = (y1 + y2)/2
    return (mx, my)

def find_center(p1, p2, p3):
    l1 = LinearEquation.from_points(p1, p2)
    l2 = LinearEquation.from_points(p2, p3)

    if l1 == l2:
        return None

    m1 = midpoint(p1, p2)
    m2 = midpoint(p2, p3)

    l3 = l1.from_slope_point(l1.perpendicular_slope(), m1)
    l4 = l2.from_slope_point(l2.perpendicular_slope(), m2)

    return l3.intersection(l4)

def dist(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)

class Circle:
    def __init__(self, center: Tuple[float, float], radius: float):
        self.center = center
        self.radius = radius

    @classmethod
    def from_points(
        cls,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float]
    ) -> Self:

        c = find_center(p1, p2, p3)
        assert c is not None, "Three points defining a circle " \
            f"must not be collinear, however received {p1}, {p2}, {p3}"

        r = dist(c, p1)

        return cls(r, c)

    @classmethod
    def from_sample(
        cls,
        arr
    ) -> Self:

        if not isinstance(arr, np.ndarray):
            try:
                arr = np.array(arr)
            except TypeError as e:
                print("Expected to be able to convert arr to a " \
                    f"numpy array, instead got: {e}")
        assert arr.shape[1] == 2, "Points must be 2-dimensional, " \
            f"but got {arr.shape[0]} for point dimension."
        assert arr.shape[0] >= 3, "Must provide at least 3 points to fit a circle."
        assert np.unique(arr, axis = 0).shape[0] >= 3, "Must provide at least 3 unique " \
            "points to fit a circle. Your dataset included duplicated points."

        x, y = arr[:, 0], arr[:, 1]
        A = np.vstack([2*x, 2*y, np.ones(len(x))]).T
        v = x**2 + y**2

        cx, cy, c3 = np.linalg.lstsq(A.T @ A, A.T @ v, rcond = None)[0]

        r = np.sqrt(c3 + cx**2 + cy**2)

        return cls((float(cx), float(cy)), float(r))

class CircularRANSACFit(Circle):
    min_num_points = 3

    def __init__(self, center: Tuple[float, float], radius: float):
        super().__init__(center, radius)

    @classmethod
    def fit(cls, arr) -> Self:
        return cls.from_sample(arr)

    def inliers(self, points, threshold):
        cx, cy = self.center
        r = self.radius
        dists = points - np.array([cx, cy])
        dists = np.sqrt(np.sum(dists**2, axis = -1))
        inlier_args = np.argwhere((dists > (r - threshold)) & (dists < (r + threshold)))
        return points[inlier_args,:].squeeze()

class Sampler:
    def __init__(self, points, num_points: int, num_samples: int):
        """
        This object acts as a interable across a number of samples.
        """
        if not isinstance(points, np.ndarray):
            try:
                points = np.array(points)
            except TypeError as e:
                print("Expected to be able to convert points to a " \
                    f"numpy array, instead got: {e}")
        self.points = points
        self.num_points = num_points
        self.num_samples = num_samples
        self.data_size = self.points.shape[0]

        self.num_samples = min(comb(self.data_size, self.num_points), self.num_samples)

        # Ensure unique samples
        sample = set()
        while len(sample) < self.num_samples:
            indexes = tuple(sorted(random.sample(range(self.data_size), self.num_points)))
            sample.add(indexes)
        sample = list(sample)
        self.sampled_set = [list(item) for item in sample]

    def __len__(self):
        return len(self.sampled_set)

    def __getitem__(self, ind):
        return np.array(self.points[self.sampled_set[ind],:])

def default_criterion(object, fits, points, threshold, num_inliers, num_objects=None):
    """
    This function acts as a default criterion for picking which fitted objects to
    accept from the RANSAC fit.

    Args:
        object: An object that can be fit to a set of points.
        fits: A list of lists, which contain the fitted object and its inliers.
        points: The complete set of points on which RANSAC is being fit.
        threshold: The threshold around which to consider points as being inliers.
        num_inliers: A number of inliers to consider being a real object.
        num_objects: A hard maximum of the number of objects to keep. Defaults to 1.

    Returns:
        fits: A list of lists, which contain the fitted object and its inliers.
    """

    # The last fit in the list is the most recent.
    prev_fit = fits.pop(-1)
    prev_inliers = prev_fit[1]

    # note: not sure if this is a good idea
    if len(prev_inliers) < object.min_num_points:
        return [*fits, prev_fit]

    # Fit it again on the set of inliers until it stops improving the fit.
    fitted = object.fit(prev_inliers)
    inliers = fitted.inliers(points, threshold)
    while inliers.shape[0] > prev_inliers.shape[0]:
        prev_fit = fitted
        prev_inliers = inliers
        fitted = object.fit(prev_inliers)
        inliers = fitted.inliers(points, threshold)

    # If the inlier set of the latest fit is too small, just return the
    # list without it.
    if inliers.shape[0] < num_inliers:
        return fits

    # Check that all of the fitted objects are unique.
    fits.append([fitted, inliers])
    unique = [item[0] for item in fits]
    unique = set(unique)
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

def convert_to_index(inliers, points):
    indexes = []
    for point in inliers:
        indexes.append(np.where((points == point).all(axis=1))[0])
    return np.array(indexes)


def eliminate_similar_by_inliers(shared_threshold=0.1, **kwargs):
    # Used to eliminate circles found by RANSAC if they are fitting similar
    # inlier sets.
    fits = kwargs["fits"]
    points = kwargs["points"]

    eliminate = []
    temp_fits = [[item[0], convert_to_index(item[1], points)] for item in fits]
    count = 1
    for i, fit1 in enumerate(temp_fits):
        inliers1 = fit1[1]
        size1 = inliers1.size
        for j, fit2 in enumerate(temp_fits[i + 1 :]):
            inliers2 = fit2[1]
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


class CircularRANSAC:
    def __init__(self, points):
        """
        Creates a RANSAC instance that acts on a set of points.

        Args:
            points: The set of points to fit a RANSAC object to.
        """
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
        num_points,
        num_samples,
        threshold,
        num_inliers,
        criterion=default_criterion,
        hook=eliminate_similar_by_inliers,
    ):
        """
        Fits an object via the RANSAC method.

        Args:
            object: The object to fit data to.
            num_points: The number of points to fit to. If this is less than the
                        number of points required by the object, this number will
                        be automatically set to that number.
            num_samples: How any RANSAC samples to use.
            threshold: The threshold of the margin to search for inliers.
            num_inliers: The number of inliers required to consider the object to
                         be a correct fit.
            criterion: A function that takes the arguments object, fits, points,
                       threshold, and num_inliers.
            hook: An optional post-processing set to further refine the fits.

        Returns:
            fits: A list of lists. Each sublist contains a fitted object found by
                  RANSAC and its inlier set of points.
        """

        if num_points < CircularRANSACFit.min_num_points:
            num_points = CircularRANSACFit.min_num_points

        sampler = Sampler(self.points, num_points, num_samples)
        fits = []
        for i, point_set in enumerate(sampler):
            fit_object = CircularRANSACFit.fit(point_set)
            inliers = fit_object.inliers(self.points, threshold)

            fits.append([fit_object, inliers])
            fits = criterion(CircularRANSACFit, fits, self.points, threshold, num_inliers)

        if hook is not None:
            args = {
                "object": CircularRANSACFit,
                "fits": fits,
                "points": self.points,
                "num_points": num_points,
                "num_samples": num_samples,
                "threshold": threshold,
                "num_inliers": num_inliers,
            }
            return hook(**args)
        return fits
