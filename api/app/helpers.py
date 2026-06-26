"""Helper functions for working with images and masks between the backend, database, and frontend."""

import cv2
import io
import numpy as np
from PIL import Image
from PIL.Image import Image as PILImage


def encode_mask(mask: np.ndarray) -> bytes:
    """Encodes a mask.

    Saves to a byte array in PNG format for storage in database.

    Args:
        mask: NumPy array of mask to encode.

    Returns:
        Bytes containing PNG image of mask.
    """
    buf = io.BytesIO()
    Image.fromarray(mask).save(buf, format="png")
    return buf.getvalue()


def decode_mask(mask: bytes) -> np.ndarray:
    """Decodes a mask.

    Opens image from bytes as NumPy boolean array, to use when pulling masks from the database.

    Args:
        mask: Bytes containing PNG mask from database.

    Returns:
        NumPy boolean array of mask.
    """
    return np.array(Image.open(io.BytesIO(mask)), dtype=np.bool)


def encode_img(img: np.ndarray) -> bytes:
    """Encodes an image as bytes in JPEG format (see encode_mask)."""
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="jpeg")
    return buf.getvalue()


def decode_img(img: bytes) -> np.ndarray:
    """Decodes JPEG image bytes to NumPy array (see decode_mask)."""
    return np.array(Image.open(io.BytesIO(img)))


def make_transparent_mask(mask: np.ndarray | bytes) -> np.ndarray | bytes:
    """Creates a transparent mask for easy overlay on an image.

    If the provided mask is encoded, will decode then re-encode for return.
    Note: If you want to change the color displayed for annotations on the frontend, this is the
    place to do it.

    Args:
        mask: Input mask

    Returns:
        Mask in uint8 format with solid white foreground and transparent background.
    """
    encoded = False
    if isinstance(mask, bytes):
        encoded = True
        mask = decode_mask(mask)

    # convert bool mask to uint8 and make true pixels white
    transparent = mask.astype(np.uint8)
    transparent[transparent > 0] = 255

    # add alpha channel and make black pixels transparent so we can overlay mask on FE
    transparent = cv2.cvtColor(transparent, cv2.COLOR_GRAY2RGBA)
    transparent[transparent[:, :, 0] == 0] = 0

    return transparent if not encoded else encode_mask(transparent)


def overlay_mask(mask: np.ndarray, img: np.ndarray) -> np.ndarray:
    """Overlays a transparent mask on an image.

    Intended to mirror the way the frontend HTML canvas overlays the transparent mask. Used for
    thumbnails with annotations displayed.

    Args:
        mask: Mask to overlay on image (output from make_transparent_mask)
        img: Image to overlay mask on top of

    Returns:
        NumPy array of image with transparent mask overlayed.
    """
    img_alpha = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
    resized_mask, _ = resize_with_scaling_factor(mask, img.shape[0])
    display_mask: np.ndarray = make_transparent_mask(resized_mask)

    # overlay resized transparent mask on top of thumbnail, same as how it is presented in frontend
    # in AnnotateCanvas.
    mask_rgb = display_mask[:, :, :3].astype(float)
    mask_alpha = (display_mask[:, :, 3:4] / 255.0) * 0.5

    result = mask_alpha * mask_rgb + (1 - mask_alpha) * img_alpha[:, :, :3]
    result = result.clip(0, 255).astype(np.uint8)

    return result


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


def resize_with_scaling_factor(
    image: PILImage | np.ndarray, longest_side: int
) -> tuple[PILImage | np.ndarray, float]:
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


def make_greyscale(
    image: np.ndarray | PILImage, weights=[0.2125, 0.7154, 0.0721]
) -> np.ndarray | PILImage:
    """
    Makes an image grayscale.

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
