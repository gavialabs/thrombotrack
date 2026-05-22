import io
import numpy as np
from PIL import Image


def encode_mask(mask: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(mask).save(buf, format="png")
    return buf.getvalue()


def decode_mask(mask: bytes) -> np.ndarray:
    return np.array(Image.open(io.BytesIO(mask)), dtype=np.bool)


def encode_img(img: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="jpeg")
    return buf.getvalue()


def decode_img(img: bytes) -> np.ndarray:
    return np.array(Image.open(io.BytesIO(img)))
