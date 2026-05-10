import argparse
import time
import csv
# import cv2
import json
import numpy as np
import matplotlib.pyplot as plt
from enum import Enum
from PIL import Image
# from skimage.draw import polygon2mask
# from sklearn.cluster import KMeans
# from tqdm import tqdm
# from shapely.geometry import MultiPolygon, Point, Polygon
# from skimage.morphology import dilation, flood

# from research.annotations.annotations import Annotations
# from research.img_utils import get_window_around_point, random_bounding_mask, iou, sample_within_contour, morphological_open_close
# from research.clustering.clustering import cluster_image, smart_flood_fill

def cluster_image(
    img: np.ndarray,
    k: int,
    # seed: Sequence | None = None,
    seed: any,
    fixed_center: bool = False,
    neighborhood_size: int = 2,
    grayscale_weights=[0.8, 0.2, 0],
    blur: int = 5,
) -> np.ndarray:
    if seed is not None:
        y, x = seed

    gray = make_greyscale(img, grayscale_weights)
    eq = cv2.equalizeHist(gray)
    blurred = cv2.GaussianBlur(eq, (blur, blur), cv2.BORDER_DEFAULT)
    img = blurred

    flattened = img.reshape((-1, 1)).astype(np.float32)

    if not fixed_center:
        init_y = np.random.choice(np.arange(img.shape[0]), size=k - 1, replace=False)
        init_x = np.random.choice(np.arange(img.shape[1]), size=k - 1, replace=False)

    if seed is not None:
        if neighborhood_size > 0:
            neighborhood = img[
                y - neighborhood_size // 2 : y + neighborhood_size // 2,
                x - neighborhood_size // 2 : x + neighborhood_size // 2,
            ]
            avg = neighborhood.mean(axis=0).mean(axis=0, keepdims=1)
        else:
            avg = img[y,x]
    
    kmeans = KMeans(
        n_clusters=k,
        init=(
            np.vstack((avg, *img[init_y, init_x])) if not fixed_center and seed is not None else "k-means++"
        ),
    ).fit(flattened, fixed_center=avg if fixed_center and seed is not None else None)
    labels = kmeans.labels_
    centers = kmeans.cluster_centers_.astype(np.uint8)

    segmented_data = centers[labels.flatten()]
    clustered_img = segmented_data.reshape((img.shape[:2]))

    return clustered_img, img, centers

class Segmentor:
    def __init__(self, img: np.ndarray, mask: np.ndarray | None) -> None:
        self.img = img
        self.mask = mask if mask else np.zeros(img[2:])
        self.kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    def segment(self, x1: int, y1: int, x2: int | None, y2: int | None, k: int) -> int:
        if x2 and y2:
            clustered, _, _ = cluster_image(self.img[y1:y2, x1:x2], k)
        
        dominant_center = np.min(clustered[clustered > 0])
        clustered[clustered != dominant_center] = 0

        opening = cv2.morphologyEx(clustered, cv2.MORPH_OPEN, self.kernel)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, self.kernel)

        self.mask |= closing
        
        return np.count_nonzero(closing)
