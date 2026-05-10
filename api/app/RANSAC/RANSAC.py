from .sampler import Sampler
from ..fitting_objects.linear_equation import LinearRANSACFit
from ..fitting_objects.circles import CircularRANSACFit
import numpy as np
from tqdm import tqdm


def default_criterion(object, fits, points, threshold, num_inliers, num_objects=1):
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


class RANSAC:
    def __init__(self, points, verbose=False, every=20):
        """
        Creates a RANSAC instance that acts on a set of points.

        Args:
            points: The set of points to fit a RANSAC object to.
            verbose: Boolean, whether to print fit progress.
            every: Integer to print verbose statement every number of interations.
        """
        if not isinstance(points, np.ndarray):
            try:
                points = np.array(points)
            except TypeError as e:
                print(
                    "Expected to be able to convert points to a "
                    f"numpy array, instead got: {e}"
                )
        self.points = points
        self.verbose = verbose
        self.every = every

    def fit(
        self,
        object,
        num_points,
        num_samples,
        threshold,
        num_inliers,
        criterion=None,
        hook=None,
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

        assert hasattr(object, "min_num_points"), (
            "Object used to fit a "
            'RANSAC instance must have the "min_num_points" attribute.'
        )
        assert hasattr(object, "fit") and callable(
            getattr(object, "fit")
        ), 'Object used to fit a RANSAC instance must have a "fit" method.'
        assert hasattr(object, "inliers") and callable(
            getattr(object, "inliers")
        ), 'Object used to fit a RANSAC instance must have an "inliers" method.'

        if num_points < object.min_num_points:
            print(
                "Fewer points than necessary to fit object were provided. "
                f"Defaulting to {object.min_num_points} points."
            )
            num_points = object.min_num_points

        if criterion is None:
            print(
                "No criterion for choosing best fits provided. Defaulting "
                "to choosing fit with the most inliers."
            )
            criterion = default_criterion

        sampler = Sampler(self.points, num_points, num_samples)
        if self.verbose:
            sampler = tqdm(sampler)
        fits = []
        for i, point_set in enumerate(sampler):
            fit_object = object.fit(point_set)
            inliers = fit_object.inliers(self.points, threshold)

            fits.append([fit_object, inliers])
            fits = criterion(object, fits, self.points, threshold, num_inliers)
            if self.verbose and (i == 0 or (i + 1) % self.every == 0):
                sampler.set_description(f"RANSAC at interation {i + 1}/{num_samples}")

        if hook is not None:
            args = {
                "object": object,
                "fits": fits,
                "points": self.points,
                "num_points": num_points,
                "num_samples": num_samples,
                "threshold": threshold,
                "num_inliers": num_inliers,
            }
            return hook(**args)
        return fits


class EdgeRANSAC(RANSAC):
    def __init__(self, edges, verbose=False, every=20):
        """
        RANSAC instance that takes an matrix representing the image edges.
        Wraps around regular RANSAC.

        Args:
            edges: A binary matrix representing the edges of an image extracted
                   through a Canny filter, or similar.
            verbose: Boolean, whether to print fit progress.
            every: Integer to print verbose statement every number of interations.
        """
        super().__init__(binary_array_to_xy(edges), verbose, every)


class LinearRANSAC(EdgeRANSAC):
    def __init__(self, edges, verbose=False, every=20):
        super().__init__(edges, verbose, every)

    def fit(
        self, num_points, num_samples, threshold, num_inliers, criterion=None, hook=None
    ):
        return super().fit(
            LinearRANSACFit,
            num_points,
            num_samples,
            threshold,
            num_inliers,
            criterion,
            hook,
        )


class CircularRANSAC(EdgeRANSAC):
    def __init__(self, edges, verbose=False, every=20):
        super().__init__(edges, verbose, every)

    def fit(
        self, num_points, num_samples, threshold, num_inliers, criterion=None, hook=None
    ):
        return super().fit(
            CircularRANSACFit,
            num_points,
            num_samples,
            threshold,
            num_inliers,
            criterion,
            hook,
        )
