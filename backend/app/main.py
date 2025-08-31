from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
import json

from .config import settings
from .schemas import ChatResponse, Usage
from .services.images import load_image_from_bytes
from .services.inference import run_chat
from .services.vlm import stream_chat_once

app = FastAPI(title="ValorMM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(""),
    history: str = Form("[]"),
    model_id: str = Form(settings.model_id),
    quant_4bit: bool = Form(settings.quant_4bit),
    use_cpu: bool = Form(settings.use_cpu),
    max_image_edge: int = Form(settings.max_image_edge),
    max_new_tokens: int = Form(settings.max_new_tokens),
    files: Optional[List[UploadFile]] = File(None),
):
    try:
        try:
            hist = json.loads(history) if history else []
            if not isinstance(hist, list): hist = []
        except Exception:
            hist = []

        imgs, pdfs = [], []
        if files:
            for f in files:
                b = await f.read()
                if f.filename.lower().endswith(".pdf") or (f.content_type or "").lower() == "application/pdf":
                    pdfs.append(b)
                else:
                    try:
                        imgs.append(load_image_from_bytes(b))
                    except Exception:
                        pass

        answer, usage = run_chat(
            model_id=model_id, quant_4bit=quant_4bit, use_cpu=use_cpu,
            max_image_edge=max_image_edge, max_new_tokens=max_new_tokens,
            history=hist, message=message or "", images=imgs, pdfs=pdfs
        )
        return ChatResponse(answer=answer, usage=Usage(**usage))
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/v1/chat/stream")
async def chat_stream(
    message: str = Form(""),
    history: str = Form("[]"),
    model_id: str = Form(settings.model_id),
    quant_4bit: bool = Form(settings.quant_4bit),
    use_cpu: bool = Form(settings.use_cpu),
    max_image_edge: int = Form(settings.max_image_edge),
    max_new_tokens: int = Form(settings.max_new_tokens),
    files: Optional[List[UploadFile]] = File(None),
):
    # Same parsing as /chat, but we return a streaming response (SSE-like)
    try:
        try:
            hist = json.loads(history) if history else []
            if not isinstance(hist, list): hist = []
        except Exception:
            hist = []

        imgs, pdfs = [], []
        if files:
            for f in files:
                b = await f.read()
                if f.filename.lower().endswith(".pdf") or (f.content_type or "").lower() == "application/pdf":
                    pdfs.append(b)
                else:
                    try:
                        imgs.append(load_image_from_bytes(b))
                    except Exception:
                        pass

        # Convert PDFs to images here to reuse vlm's streaming directly
        if pdfs:
            from .services.pdf import pdf_to_images
            for pb in pdfs:
                imgs.extend(pdf_to_images(pb))

        def sse_iter():
            for chunk in stream_chat_once(
                model_id=model_id, quant_4bit=quant_4bit, use_cpu=use_cpu,
                max_image_edge=max_image_edge, max_new_tokens=max_new_tokens,
                history=hist, user_text=message or "", images=imgs
            ):
                # Simple text chunks; front-end will append directly
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(sse_iter(), media_type="text/event-stream")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
