"""Defines database object enums and tuning variables used for cropping and segmentation."""

import enum
import numpy as np


class OxygenatorType(str, enum.Enum):
    HLS = "hls"
    NAUTILUS = "nautilus"


class AnnotationType(str, enum.Enum):
    CLOT = "clot"
    FIBRIN = "fibrin"
    ERASE = "erase"


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "heic"}

# Oxygenator detection/cropping
HLS_SIDE_LENGTH_MM = 88
NAUTILUS_DIAMETER_MM = 87.5

# variables for tuning HLS oxygenator detection
HLS_LONGEST_SIDE = (
    1024  # how many pixels the longest side of the rescaled image of an oxygenator should be
    # before running detection algorithm
)
HLS_GAUSSIAN_BLUR = 5  # kernel size for Gaussian blur during preprocessing

HOUGH_RHO = 1  # distance resolution in pixels of the Hough grid
HOUGH_THETA = np.pi / 180  # angular resolution in radians of the Hough grid
HOUGH_THRESHOLD = 150  # minimum number of votes (intersections in Hough grid cell)
HOUGH_MIN_LINE_LENGTH = 30  # minimum number of pixels making up a line
HOUGH_MAX_LINE_GAP = 0  # maximum gap in pixels between connectable line segments

CORNER_OUTLIER_TOL = 0.8  # tolerance for removing outlier candidate corners

# variables for tuning Nautilus oxygenator detection
NAUTILUS_LONGEST_SIDE = 512
NAUTILUS_GRAYSCALE_WEIGHTS = [0, 0.5, 0.5]  # RGB weights for grayscaling original image

CIRCLE_CANNY_THRESH1 = 300  # lower threshold for Canny edge detection for circles
CIRCLE_CANNY_THRESH2 = 500  # upper threshold for Canny edge detection for circles

RANSAC_NUM_POINTS = 3  # number of points to fit each circle
RANSAC_NUM_SAMPLES = 6000  # number of samples to take during RANSAC
RANSAC_THRESHOLD = 1  # threshold of margin to search for inliers
RANSAC_NUM_INLIERS = (
    240  # number of inliers required to consider the object as correct fit
)

CIRCLE_CROP_BUFFER = 0  # buffer to extend the circle the image is being cropped to

# Segmentation

WINDOW_SIZE = 150  # size of window around seed when using point prompts
K_CLOT_POINT = 8  # number of clusters for clots with point prompts
K_FIBRIN_POINT = 6  # number of clusters for fibrin with point prompts
K_CLOT_FREEFORM = 4  # number of clusters for clots with freeform prompts
K_FIBRIN_FREEFORM = 4  # number of clusters for fibrin with freeform prompts
MORPH_KERNEL_SIZE = 3  # kernel size for morphological opening/closing during mask
# postprocessing
SEED_NEIGHBORHOOD = (
    2  # neighborhood area size for taking average of seed point to use as initial
)
# centroid
GRAYSCALE_WEIGHTS = (
    0.8,
    0.2,
    0,
)  # RGB weights for converting image patch to grayscale before clustering
BLUR_KERNEL_SIZE = 5  # kernel size for Gaussian blurring image patch before clustering
