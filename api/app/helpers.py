import cv2
import io
import numpy as np
from PIL import Image

from app.utils.img_utils import resize_with_scaling_factor


def encode_mask(mask: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(mask).save(buf, format="png")
    return buf.getvalue()


def decode_mask(mask: bytes) -> np.ndarray:
    return np.array(Image.open(io.BytesIO(mask)), dtype=np.bool)


def encode_img(img: np.ndarray, extension: str = "jpeg") -> bytes:
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format=extension)
    return buf.getvalue()


def decode_img(img: bytes) -> np.ndarray:
    return np.array(Image.open(io.BytesIO(img)))


def make_transparent_mask(mask: np.ndarray) -> np.ndarray:
    """Creates a transparent mask for easy overlay on an image.

    Note: If you want to change the color displayed for annotations on the frontend, this is the
    place to do it.

    Args:
        mask: Input mask

    Returns:
        Mask in uint8 format with solid white foreground and transparent background.
    """
    # convert bool mask to uint8 and make true pixels white
    transparent = mask.astype(np.uint8)
    transparent[transparent > 0] = 255

    # add alpha channel and make black pixels transparent so we can overlay mask on FE
    transparent = cv2.cvtColor(transparent, cv2.COLOR_GRAY2RGBA)  # type: ignore
    transparent[transparent[:, :, 0] == 0] = 0

    return transparent


def overlay_mask(mask: np.ndarray, img: np.ndarray) -> np.ndarray:
    img_alpha = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
    resized_mask, _ = resize_with_scaling_factor(mask, img.shape[0])
    display_mask = make_transparent_mask(resized_mask)

    # overlay resized transparent mask on top of thumbnail, same as how it is presented in frontend
    # in AnnotateCanvas.
    mask_rgb = display_mask[:, :, :3].astype(float)
    mask_alpha = (display_mask[:, :, 3:4] / 255.0) * 0.5

    result = mask_alpha * mask_rgb + (1 - mask_alpha) * img_alpha[:, :, :3]
    result = result.clip(0, 255).astype(np.uint8)

    return result
