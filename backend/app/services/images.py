from typing import List
from io import BytesIO
from PIL import Image, ImageOps

def load_image_from_bytes(b: bytes) -> Image.Image:
    im = Image.open(BytesIO(b))
    try:
        im = ImageOps.exif_transpose(im)  # auto-orient
    except Exception:
        pass
    return im.convert("RGB")

def resize_long_edge(im: Image.Image, max_edge: int = 1024) -> Image.Image:
    w, h = im.size
    long_edge = max(w, h)
    if long_edge <= max_edge:
        return im
    scale = max_edge / long_edge
    new_w, new_h = int(w * scale), int(h * scale)
    return im.resize((new_w, new_h), Image.LANCZOS)
