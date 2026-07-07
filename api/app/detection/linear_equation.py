"""Module for representing lines detected in oxygenator images."""

import math

try:
    from typing import Self
except:
    from typing_extensions import Self


def find_slope(p1: tuple[float, float], p2: tuple[float, float]) -> float | None:
    """Returns the slope of a line defined by 2 points.

    Args:
        p1: x, y coordinates of point 1.
        p2: x, y coordinates of point 2.

    Returns:
        (y2 - y1)/(x2 - x1) or None if the line is vertical.
    """
    x1, y1 = p1
    x2, y2 = p2

    if x2 - x1 == 0:
        return None

    return (y2 - y1) / (x2 - x1)


def find_intercept(p: tuple[float, float], slope: float | None) -> float:
    """Returns the intercept of a line given a point p and slope.

    Args:
        p: x, y coordinates of a point on the line.
        slope: slope of the desired line.

    Returns:
        y - slope * x or x if the line is vertical.
    """
    x, y = p

    if slope is None:
        return x

    return y - slope * x


def dist(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Returns the Euclidean distance between two points.

    Args:
        p1: point 1.
        p2: point 2.

    Returns:
        Euclidean distance between the points.
    """
    x1, y1 = p1
    x2, y2 = p2

    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


class LinearEquation:
    """Describes a line.

    Attributes:
        slope: Slope of the line.
        intercept: y-intercept of the line.
    """

    def __init__(self, slope: float | None, intercept: float):
        """
        Constructs a 2-D linear equation using a slope and intercept.

        Args:
            slope: A float representing the slope of a line. Can be None for vertical lines.
            intercept: y-intercept of the line.
        """
        self.slope = slope
        if slope is None:
            self.intercept: tuple[float, float] = (intercept, 0)
        else:
            self.intercept = (0, intercept)

    @classmethod
    def from_points(cls, p1: tuple[float, float], p2: tuple[float, float]) -> Self:
        """Constructs linear equation using two points."""
        slope = find_slope(p1, p2)
        intercept = find_intercept(p1, slope)
        return cls(slope, intercept)

    @classmethod
    def from_slope_point(cls, slope: float, p: tuple[float, float]) -> Self:
        """Constructs linear equation given a slope and an arbitrary point."""
        intercept = find_intercept(p, slope)
        return cls(slope, intercept)

    def get_y(self, x: float) -> float | None:
        """Returns the y value for a given x."""
        if self.slope is None:
            return None

        return x * self.slope + self.intercept[1]

    def intersection(self, other) -> tuple[float, float | None] | None:
        """Finds the intersection point of two LinearEquations."""
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

        x = (self.intercept[1] - other.intercept[1]) / (other.slope - self.slope)
        y = (self.slope * x) + self.intercept[1]

        return (x, y)

    def perpendicular_slope(self) -> float:
        """Returns the opposite reciprocal of the line's slope, or 0 if it is vertical."""
        if self.slope is None:
            return 0

        return -1 / self.slope

    def __eq__(self, other):
        if isinstance(other, LinearEquation):
            if other.slope is None and self.slope is None:
                return self.intercept[0] == other.intercept[0]
            elif other.slope is not None and self.slope is not None:
                return (self.slope == other.slope) and (
                    self.intercept[1] == other.intercept[1]
                )
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
