import cv2
import numpy as np
from typing import Sequence
from flask import current_app as app
from PIL import Image
from sklearn.cluster import KMeans
from skimage.draw import ellipse, polygon2mask
from skimage.segmentation import flood

from ..utils.img_utils import make_greyscale
from ..models import ThrombusType, Point

WINDOW_SIZE = 150
K_CLOT_POINT = 8
K_FIBRIN_POINT = 6
K_CLOT_CIRCLE = 4
K_FIBRIN_CIRCLE = 6
MORPH_KERNEL_SIZE = 3


def cluster_image(
    img: np.ndarray,
    k: int,
    seed: Sequence[int] | None = None,
    neighborhood_size: int = 2,
    grayscale_weights=[0.8, 0.2, 0],
    blur: int = 5,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if seed is not None:
        y, x = seed

    gray = make_greyscale(img, grayscale_weights)
    eq = cv2.equalizeHist(gray)
    blurred = cv2.GaussianBlur(eq, (blur, blur), cv2.BORDER_DEFAULT)

    init_y = np.random.choice(np.arange(img.shape[0]), size=k - 1, replace=False)
    init_x = np.random.choice(np.arange(img.shape[1]), size=k - 1, replace=False)

    if seed is not None:
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
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

    opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)

    return closing


def smart_flood_fill(
    clustered: np.ndarray,
    processed: np.ndarray,
    seed: Sequence[int],
    preserve_seed: bool = True,
    continuous: bool = True,
) -> np.ndarray:
    # 1. flood fill on the clustered result
    mask = flood(clustered, tuple(seed)).astype(np.uint8)
    mask[mask > 0] = 255
    mask = morphological_open_close(mask)

    # 2. regular flood fill on the non-clustered image until some area is actually selected
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

    if continuous:
        # re-flood at the original seed to remove other discontinuous areas
        mask = flood(mask, tuple(seed)).astype(np.uint8)

    return mask


class Segmentor:
    def __init__(self, img: np.ndarray, mask: np.ndarray | None = None) -> None:
        self.img = img
        self.img_mask = (
            mask.copy() if mask is not None else np.zeros(img.shape[:2], dtype=np.bool)
        )

    def get_window_around_point(self, point: Sequence[int], size: int):
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
        thrombus_type: ThrombusType,
    ) -> np.ndarray:
        if len(path) == 1:
            seed = (path[0][1], path[0][0])
            window, new_center = self.get_window_around_point(seed, WINDOW_SIZE)
            clustered, processed, _ = cluster_image(
                window,
                K_CLOT_POINT if thrombus_type == ThrombusType.CLOT else K_FIBRIN_POINT,
                new_center,
            )
            thrombus_mask = smart_flood_fill(clustered, processed, new_center)

            # transfer mask for this window onto the original image
            flood_indices = np.nonzero(thrombus_mask)
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
                    K_CLOT_CIRCLE
                    if thrombus_type == ThrombusType.CLOT
                    else K_FIBRIN_CIRCLE
                ),
            )

            if thrombus_type == ThrombusType.CLOT:
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
            self.img_mask[y_min:y_max, x_min:x_max] |= thrombus_mask.astype(np.bool)

        return thrombus_mask
