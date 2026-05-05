import numpy as np
from math import *
from typing import Tuple

try:
    from typing import Self
except:
    from typing_extensions import Self

def find_slope(p1, p2):
    """
    Returns the slope of a line defined by 2 points.

    Args:
        p1: x, y coordinates of point 1.
        p2: x, y coordinates of point 2.

    Returns:
        (y2 - y1)/(x2 - x1) or None if the line in vertical.
    """
    x1, y1 = p1
    x2, y2 = p2
    if x2 - x1 == 0:
        return None
    return (y2 - y1)/(x2 - x1)

def find_intercept(p, slope):
    """
    Returns the intercept of a line given a point p and slope.

    Args:
        p: x, y coordinates of a point on the line.
        slope: slope of the desired line.

    Returns:
        y - slope * x or x if the line in vertical.
    """
    x, y = p
    if slope is None:
        return x
    return y - slope * x

def dist(p1, p2):
    """
    Returns the Euclidean distance between two points.

    Args:
        p1: point 1.
        p2: point 2.

    Returns:
        Euclidean distance between the points.
    """
    x1, y1 = p1
    x2, y2 = p2
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)

class LinearEquation:
    def __init__(self, slope: float, intercept: float):
        """
        Initiates a 2D linear equation using a slope and intercept.

        Args:
            slope: A float representing the slope of a line. Can be None for vertical lines.
            intercept:
        """
        self.slope = slope
        if self.slope is None:
            self.intercept = (intercept, 0)
        else:
            self.intercept = (0, intercept)

    @classmethod
    def from_points(cls, p1: Tuple[float, float], p2: Tuple[float, float]) -> Self:
        slope = find_slope(p1, p2)
        intercept = find_intercept(p1, slope)
        return cls(slope, intercept)

    @classmethod
    def from_slope_point(cls, slope: float, p: Tuple[float, float]) -> Self:
        intercept = find_intercept(p, slope)
        return cls(slope, intercept)

    @classmethod
    def from_sample(cls, arr) -> Self:
        if not isinstance(arr, np.ndarray):
            try:
                arr = np.array(arr)
            except TypeError as e:
                print("Expected to be able to convert arr to a " \
                    f"numpy array, instead got: {e}")
        assert arr.shape[1] == 2, "Points must be 2-dimensional, " \
            f"but got {arr.shape[0]} for point dimension."
        assert arr.shape[0] >= 2, "Must provide at least 2 points to fit a line."
        assert np.unique(arr, axis = 0).shape[0] >= 2, "Must provide at least 2 unique " \
            "points to fit a line. Your dataset included duplicated points."

        x = arr[:,0]
        y = arr[:,1]
        A = np.vstack([x, np.ones(len(x))]).T
        m, c = np.linalg.lstsq(A, y, rcond = None)[0]
        mse_l = np.mean(((m * x + c) - y)**2)

        # Vertical line might fit better, but is not able to be fit with lstsq
        vert = np.mean(x)
        mse_v = np.mean((x - vert)**2)

        if mse_v < mse_l:
            return cls(None, float(vert))

        return cls(float(m), float(c))

    def get_x(self, y):
        # Returns the x value for a given y
        if self.slope is None:
            return self.intercept[0]
        if self.slope == 0:
            return None
        return (y - self.intercept[1])/self.slope

    def get_y(self, x):
        # Returns the y value for a given x
        if self.slope is None:
            return None
        return x * self.slope + self.intercept[1]

    def angle(self):
        # Returns the angle of the line relative to the x-axis in radians
        x1, y1 = self.intercept
        x2, y2 = x1 + 1, y1 + self.slope
        return atan2((y2 - y1), (x2 - x1))

    def intersection(self, other):
        # Find the intersection point of two LinearEquations
        if not isinstance(other, LinearEquation):
            raise TypeError("Must pass a linear equation to find intersection.")
        if self.slope is None:
            if other.slope is None:
                return None
            return (self.intercept[0], other.get_y(self.intercept[0]))
        if other.slope is None:
            return other.intersection(self)
        if self.slope == other.slope:
            return None
        x = (self.intercept[1] - other.intercept[1])/(other.slope - self.slope)
        y = (self.slope * x) + self.intercept[1]
        return (x, y)

    def perpendicular_slope(self):
        if self.slope is None:
            return 0
        return -1/self.slope

    def __eq__(self, other):
        if isinstance(other, LinearEquation):
            if other.slope is None and self.slope is None:
                return self.intercept[0] == other.intercept[0]
            elif other.slope is not None and self.slope is not None:
                return (self.slope == other.slope) and (self.intercept[1] == other.intercept[1])
        return False

    def __hash__(self):
        return hash((self.slope, self.intercept[0], self.intercept[1]))

    def __str__(self):
        if self.slope is None:
            return "x = {:g}".format(self.intercept[0])
        if self.slope == 1:
            if self.intercept[1] == 0:
                return "y = x"
            return "y = x + {:g}".format(self.intercept[1])
        if self.intercept[1] == 0:
            return "y = {:g}x".format(self.slope)
        if self.slope == 0:
            return "y = {:g}".format(self.intercept[1])
        return "y = {:g}x + {:g}".format(self.slope, self.intercept[1])

class LineSegment:
    def __init__(self, p1: Tuple[float, float], p2: Tuple[float, float]):
        self.p1 = p1
        self.p2 = p2
        self.equation = LinearEquation(self.p1, self.p2)

    def check_in_bounds(self, point: Tuple[float, float]):
        # Checks that a point is in the LineSegment range
        x, y = point
        if (x < self.p1[0] and x < self.p2[0]) or (x > self.p1[0] and x > self.p2[0]):
            return False
        elif (y < self.p1[1] and y < self.p2[1]) or (y > self.p1[1] and y > self.p2[1]):
            return False
        return True

    def get_x(self, y: float):
        # Returns the x value for a given y
        x = self.p1[0]
        if not self.check_in_bounds(x, y):
            return None
        return self.equation.get_x(y)

    def get_y(self, x: float):
        # Returns the y value for a given x
        y = self.p1[1]
        if not self.check_in_bounds((x, y)):
            return None
        return self.equation.get_y(x)

    def angle(self):
        # Returns the angle of the line segment relative to the x-axis in radians
        x1, y1 = self.p1
        x2, y2 = self.p2
        return atan2((y2 - y1), (x2 - x1))

    def length(self):
        return dist(self.p1, self.p2)

class LinearRANSACFit(LinearEquation):
    min_num_points = 2

    def __init__(self, slope: float, intercept: float):
        super().__init__(slope, intercept)

    @classmethod
    def fit(cls, arr) -> Self:
        return cls.from_sample(arr)

    def inliers(self, points, threshold):
        if self.slope is None:
            x = self.intercept[0]
            x_s = points[:,0]
            inlier_args = np.where((x_s > x - threshold) & \
                (x_s < x+threshold))
            return points[inlier_args,:].squeeze()
        theta = self.angle()
        if theta > np.pi/2:
            theta -= np.pi/2
        adjusted_threshold = threshold/np.cos(theta)
        x,y = points[:,0], points[:,1]
        y_pred = self.slope * x + self.intercept[1]

        inlier_args = np.where((y > y_pred-adjusted_threshold) & \
            (y < y_pred+adjusted_threshold))
        return points[inlier_args,:].squeeze()

    def as_linear_equation(self):
        if self.slope is None:
            return LinearEquation(None, self.intercept[0])
        return LinearEquation(self.slope, self.intercept[1])
