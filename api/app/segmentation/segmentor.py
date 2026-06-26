"""Module for segmenting oxygenator images to create Annotations."""

import cv2
import numpy as np
from typing import Sequence
from sklearn.cluster import KMeans
from skimage.draw import ellipse, polygon2mask
from skimage.segmentation import flood

from app.constants import *
from app.helpers import decode_mask, make_greyscale
from app.models import AnnotationType, Annotation

def cluster_image(
    img: np.ndarray,
    k: int,
    seed: np.ndarray | None = None,
    neighborhood_size: int = SEED_NEIGHBORHOOD,
    grayscale_weights: tuple[float, float, float] = GRAYSCALE_WEIGHTS,
    blur: int = BLUR_KERNEL_SIZE,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Clusters an image.

    Makes the image grayscale using provided or default weights to enhance contrast between blood
    and clotting/fibrin and remove glare from plastic. Equalizes the grayscale image's histogram to
    dramatically increase contrast between blood and clotting/fibrin. Blurs the image to reduce
    noise from dust on the oxygenator window. If a seed is given, uses the neighborhood size around
    the seed to get an average color as one of the initial centroids. Otherwise, uses default
    k-means++ centroid initialization. Clusters the image and returns the clustered, blurred, and
    final centroids.

    Args:
        img: Image patch array to cluster.
        k: Number of clusters.
        seed: Point prompt on image (if exists).
        neighborhood_size: Side length of square around seed point for initial centroid.
        grayscale_weights: Tuple R, G, B weights when converting to grayscale (R + G + B = 1.0)
        blur: Side length of kernel for Gaussian blur.

    Returns:
        Clustered image array, preprocessed image, and final centroids.
    """
    if seed is not None:
        y, x = seed

    gray = make_greyscale(img, grayscale_weights)
    eq = cv2.equalizeHist(gray)
    blurred = cv2.GaussianBlur(eq, (blur, blur), cv2.BORDER_DEFAULT)

    init_y = np.random.choice(np.arange(img.shape[0]), size=k - 1, replace=False)
    init_x = np.random.choice(np.arange(img.shape[1]), size=k - 1, replace=False)

    if seed is not None:
        # point prompt was used-- set an initial centroid to a neighborhood around seed
        if neighborhood_size > 0:
            neighborhood = blurred[
                y - neighborhood_size // 2 : y + neighborhood_size // 2,
                x - neighborhood_size // 2 : x + neighborhood_size // 2,
            ]
            avg = neighborhood.mean(axis=0).mean(axis=0, keepdims=1)
        else:
            avg = blurred[y, x]

    flattened = blurred.reshape((-1, 1)).astype(np.float32)

    kmeans = KMeans(
        n_clusters=k,
        init=(
            np.vstack((avg, *blurred[init_y, init_x]))
            if seed is not None
            else "k-means++"
        ),
    ).fit(flattened)
    labels = kmeans.labels_
    centers = kmeans.cluster_centers_.astype(np.uint8)

    segmented_data = centers[labels.flatten()]
    clustered_img = segmented_data.reshape((img.shape[:2]))

    return clustered_img, blurred, centers.flatten()


def morphological_open_close(
    img: np.ndarray, kernel_size: int = MORPH_KERNEL_SIZE
) -> np.ndarray:
    """Performs a morphological opening and closing on an array."""
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

    opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)

    return closing


def smart_flood(
    clustered: np.ndarray,
    processed: np.ndarray,
    seed: np.ndarray,
    preserve_seed: bool = True,
    contiguous: bool = True,
) -> np.ndarray:
    """Floods a clustered image at a given point and returns mask.

    Floods at the given point and performs a morphological opening and closing. If the area was
    eroded, uses the preprocessed (grayscale + histogram equalized + blurred) image to perform a
    flood with tolerance 5 and morphological opening and closing, increasing tolerance by 2 until
    area is selected. If preserve_seed, approximates mask using ellipse to include seed. If
    contiguous, re-floods at seed point to remove discontiguities (introduced by erosion).

    Args:
        clustered: Clustered image array.
        processed: Preprocessed image array from cluster_image.
        seed: Point to flood at.
        preserve_seed: Whether seed must be present in output.
        contiguous: Whether mask area must be contiguous.

    Returns:
        Mask of flooded area.
    """
    # 1. flood on the clustered result
    mask = flood(clustered, tuple(seed)).astype(np.uint8)
    mask[mask > 0] = 255
    mask = morphological_open_close(mask)

    # 2. regular flood on the non-clustered image until some area is actually selected
    tol = 5
    while np.count_nonzero(mask) == 0:
        mask = flood(processed, tuple(seed), tolerance=tol).astype(np.uint8)
        mask = morphological_open_close(mask)

        tol += 2

    if preserve_seed and mask[*seed] == 0:
        # closing got rid of the seed point in the selection
        mask_points = np.argwhere(mask == 1)
        distances = np.linalg.norm(mask_points - seed, axis=1)
        closest_index = np.argmin(distances)
        closest_point = mask_points[closest_index]

        # draw an ellipse from the closest point on the selection to the seed
        angle = np.arctan2(closest_point[0] - seed[0], closest_point[1] - seed[1])
        rr, cc = ellipse(
            closest_point[0],
            closest_point[1],
            5,
            distances[closest_index],
            rotation=-angle,
            shape=mask.shape,
        )
        mask[rr, cc] = 1
        mask[*seed] = 1

    if contiguous:
        # re-flood at the original seed to remove discontiguities
        mask = flood(mask, tuple(seed)).astype(np.uint8)

    return mask


class Segmentor:
    """Segments oxygenator images given prompts to create Annotations.

    Attributes:
        img: Original image array.
        img_mask: Mask of all segmentations of image, same size as img.
    """

    def __init__(self, img: np.ndarray, mask: np.ndarray | None = None):
        """Initializes with an image and mask."""
        self.img = img
        self.img_mask = (
            mask.copy() if mask is not None else np.zeros(img.shape[:2], dtype=np.bool)
        )

    def get_window_around_point(
        self, point: Sequence[int], size: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Returns a window up to a specified size around a point of img.

        Window size may be smaller if the point is near the boundary of the image.

        Args:
            point: Point to return window around.
            size: Side length of window.

        Returns:
            Array of the image window/patch and the relative coordinates of the center of the
            window.
        """
        y_min = max(point[0] - (size // 2), 0)
        x_min = max(point[1] - (size // 2), 0)

        window = self.img[
            y_min : point[0] + (size // 2), x_min : point[1] + (size // 2)
        ]

        # explicitly calculate this since the window size is not guaranteed near borders
        new_point = np.array([point[0] - y_min, point[1] - x_min])

        return window, new_point

    def segment(
        self,
        path: list[list[int]],
        annotation_type: AnnotationType,
    ) -> np.ndarray:
        """Segments img.

        Determines if the provided path is a point or freeform prompt. Segments img using a window
        around the given seed or using the enclosed area. Returns a mask of the segmentation area.

        Args:
            path: List of coordinates comprising the user input (drawn on the image).
            annotation_type: Whether this is a clot or fibrin annotation.

        Returns:
            Mask of newly segmented area on img (same size as img).
        """
        img_mask = np.zeros_like(self.img_mask, dtype=np.bool)

        if len(path) < min(K_CLOT_POINT, K_FIBRIN_POINT):
            seed = (path[0][1], path[0][0])
            window, new_center = self.get_window_around_point(seed, WINDOW_SIZE)
            clustered, processed, _ = cluster_image(
                window,
                (
                    K_CLOT_POINT
                    if annotation_type == AnnotationType.CLOT
                    else K_FIBRIN_POINT
                ),
                new_center,
            )
            thrombus_mask = smart_flood(clustered, processed, new_center)

            # transfer mask for this window onto the original image
            flood_indices = np.nonzero(thrombus_mask)
            img_mask[
                flood_indices[0] + (seed[0] - new_center[0]),
                flood_indices[1] + (seed[1] - new_center[1]),
            ] = np.True_
            self.img_mask[
                flood_indices[0] + (seed[0] - new_center[0]),
                flood_indices[1] + (seed[1] - new_center[1]),
            ] = np.True_
        else:
            bounds = np.flip(path)
            y_min, y_max = np.min(bounds[:, 0]), np.max(bounds[:, 0])
            x_min, x_max = np.min(bounds[:, 1]), np.max(bounds[:, 1])

            window = self.img[y_min:y_max, x_min:x_max]
            clustered, _, centers = cluster_image(
                window,
                (
                    K_CLOT_FREEFORM
                    if annotation_type == AnnotationType.CLOT
                    else K_FIBRIN_FREEFORM
                ),
            )

            if annotation_type == AnnotationType.CLOT:
                # take the darkest center
                dominant_center = np.min(centers)
            else:
                # take the lightest center
                dominant_center = np.max(centers)

            clustered[clustered != dominant_center] = 0

            # exclude outside of path
            bounds[:, 0] -= y_min - 1
            bounds[:, 1] -= x_min - 1
            path_mask = polygon2mask(clustered.shape, bounds)
            clustered[path_mask == 0] = 0

            # smooth edges and fill holes
            thrombus_mask = morphological_open_close(clustered)

            # transfer mask for this window onto the original image
            img_mask[y_min:y_max, x_min:x_max] = thrombus_mask.astype(np.bool)
            self.img_mask[y_min:y_max, x_min:x_max] |= thrombus_mask.astype(np.bool)

        return img_mask

    def erase(
        self, path: list[list[int]], existing_annotations: list[Annotation]
    ) -> tuple[np.ndarray, int, int]:
        """Erases segmented area.

        Uses provided freeform prompt to iterate over existing annotations and sums the clot/fibrin
        area from all annotations the prompt overlaps with.

        Args:
            path: List of coordinates comprising user input (drawn on image).
            existing_annotations: List of existing Annotations for this image.

        Returns:
            Mask of the area described by path, clot area being erased, and fibrin area being
            erased.
        """
        bounds = np.flip(path)
        erase_mask = polygon2mask(self.img_mask.shape, bounds)
        self.img_mask[erase_mask == 1] = 0

        for annotation in existing_annotations:
            if annotation.type != AnnotationType.ERASE:
                continue

            # if we erase on top of another erase, we don't want to double count the erased
            # clot/fibrin area
            mask = decode_mask(annotation.mask)
            erase_mask &= ~mask

        clot_area = 0
        fibrin_area = 0
        for annotation in existing_annotations:
            if annotation.type == AnnotationType.ERASE:
                continue

            mask = decode_mask(annotation.mask)
            overlap = erase_mask & mask
            area = int(np.count_nonzero(overlap))

            if annotation.type == AnnotationType.CLOT:
                clot_area += area
            else:
                fibrin_area += area

        return erase_mask, clot_area, fibrin_area
