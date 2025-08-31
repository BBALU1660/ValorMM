from typing import List
from PIL import Image
import fitz  # PyMuPDF

def pdf_to_images(pdf_bytes: bytes, dpi: int = 144) -> List[Image.Image]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    imgs = []
    for page in doc:
        pm = page.get_pixmap(dpi=dpi, alpha=False)
        img = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
        imgs.append(img)
    return imgs
