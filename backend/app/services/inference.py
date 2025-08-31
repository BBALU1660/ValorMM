from typing import List, Dict
from PIL import Image
from .pdf import pdf_to_images
from .vlm import chat_once

def run_chat(model_id: str, quant_4bit: bool, use_cpu: bool, max_image_edge: int, max_new_tokens: int,
             history: List[Dict[str,str]], message: str, images: List[Image.Image], pdfs: List[bytes]):
    # Convert PDFs to images and extend
    for pdf_bytes in pdfs:
        images.extend(pdf_to_images(pdf_bytes))
    # Call model
    return chat_once(model_id, quant_4bit, use_cpu, max_image_edge, max_new_tokens, history, message, images)
