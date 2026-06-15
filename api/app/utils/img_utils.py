import numpy as np
from PIL import Image
from PIL.Image import Image as PILImage


def rescale(
    image: PILImage | np.ndarray, scaling_factor: float
) -> PILImage | np.ndarray:
    """
    Rescales an image by a scaling factor.

    Args:
        image: either a PIL image or a numpy array to be resized.
        scaling_factor: float to resize the image dimensions by.

    Returns:
        image: rescaled image of the same type.
    """

    is_array = False
    if isinstance(image, np.ndarray):
        h, w = image.shape[:2]
        image = Image.fromarray(image)
        is_array = True
    else:
        w, h = image.size

    image = image.resize((round(w * scaling_factor), round(h * scaling_factor)))
    if is_array:
        image = np.asarray(image)
    return image


def resize_with_scaling_factor(image: PILImage | np.ndarray, longest_side: int) -> PILImage | np.ndarray:
    """
    Rescales an image by scaling its longest side to a given length.

    Args:
        image: either a PIL image or a numpy array to be resized.
        longest_side: int the new size of the image's longest side.

    Returns:
        image: resized image of the same type.
        scaling_factor: a factor by which the image is scaled, for reference.
    """
    if isinstance(image, np.ndarray):
        h, w = image.shape[:2]
    else:
        w, h = image.size

    curr_longest = max(h, w)
    scaling_factor = longest_side / curr_longest
    return rescale(image, scaling_factor), scaling_factor


def make_greyscale(image, weights=[0.2125, 0.7154, 0.0721]):
    """
    Rotates an image by a given anlge.

    Args:
        image: either a PIL image or a numpy array to be made greyscale.
        weights: a set of weights for the color channel - defaults to skimage's weights.

    Returns:
        image: greyscale image of the same type.
    """
    num_weights = len(weights)
    assert num_weights > 2, "Must supply a weight for each color channel."
    assert num_weights < 4, "Given more weights than there are color channels."

    is_array = True
    if not isinstance(image, np.ndarray):
        image = np.asarray(image)
        is_array = False

    assert len(image.shape) == 3 and image.shape[2] == 3, "Image is already greyscale."

    r, g, b = image[:, :, 0], image[:, :, 1], image[:, :, 2]
    rw, gw, bw = weights

    image = (r * rw + g * gw + b * bw).squeeze()
    image = np.uint8(image)

    if not is_array:
        image = Image.fromarray(image)

    return image
