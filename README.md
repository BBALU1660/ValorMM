# ValorMM — Local Multimodal Chat (Text + Images/PDFs)

A ChatGPT-style **web app** you run locally. Chat normally, or attach **images / PDFs** via the **“+” button**, **drag & drop**, or **Ctrl+V paste**. No paid APIs; everything runs on your machine.

- **Frontend:** Next.js 14 + React 18 + TailwindCSS
- **Backend:** FastAPI + Uvicorn
- **Model:** Qwen2-VL-2B-Instruct (vision-language, local; optional 4-bit)
- **OS/Hardware Target:** Windows 10/11, RTX 3050 Ti 4 GB VRAM, Ryzen 7 4800H, 16 GB RAM

> ✅ **No cloud keys, no usage limits.** First run downloads models to your Hugging Face cache (you can set `HF_HOME`).

---

## Demo (what you get)

- Clean, ChatGPT-style UI (dark theme)
- Single message composer with **Enter** to send, **Shift+Enter** newline
- **Attach files**: + button / drag-drop / Ctrl+V paste
- **Attachment previews** before sending (image thumbnails, PDF chips)
- **Streaming responses** (typing effect) with images/PDFs
- Markdown rendering + code highlighting

---

## Project Structure

ValorMM/
├─ backend/ # FastAPI (port 8000)
│ ├─ app/
│ │ ├─ main.py # routes: /health, /api/v1/chat, /api/v1/chat/stream (SSE)
│ │ ├─ config.py # defaults (model id, quant, tokens, image size)
│ │ ├─ schemas.py # response models
│ │ ├─ services/
│ │ │ ├─ vlm.py # Qwen2-VL loader + non-stream + streaming
│ │ │ ├─ images.py # load/resize images
│ │ │ └─ pdf.py # PDF → images (PyMuPDF)
│ │ └─ utils/tokens.py # (placeholder)
│ ├─ requirements.txt
│ └─ run_dev.ps1 # uvicorn launcher
└─ frontend/ # Next.js (port 3000)
├─ app/
│ ├─ layout.tsx # imports global styles
│ ├─ globals.css # theme + markdown styles
│ └─ page.tsx # Chat UI (streaming + attachments)
├─ package.json, tailwind.config.js, ...

yaml
Copy code

---

## Requirements

- **Python 3.10+**
- **Node.js LTS** (18+ recommended)
- **CUDA 12.1 runtime** (for GPU; otherwise CPU fallback)
- **PyTorch CUDA 12.1 wheels** (installed via script below)
- Optional: set cache path:  
  ```powershell
  setx HF_HOME "C:\hf_cache"
Install & Run
1) Backend (first time)
powershell
Copy code
# Open a new PowerShell in ValorMM\backend
cd .\backend\
python -m venv .venv
. .\.venv\Scripts\Activate
python -m pip install --upgrade pip

# PyTorch (CUDA 12.1 for RTX 30-series)
pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio

# App deps
pip install -r requirements.txt

# Start API
.\run_dev.ps1
# -> http://127.0.0.1:8000  (health: /health)
2) Frontend
powershell
Copy code
# In a second terminal
cd .\frontend\
npm install
npm run dev
# -> http://localhost:3000
Usage
Text-only: just type and press Enter.

Attach files: click +, drag files into the window, or Ctrl+V paste.

Preview: thumbnails (images) and chips (PDFs) appear above the composer.

Send: hit Enter or click Send. The assistant streams the reply.

API Reference (local)
POST /api/v1/chat
Body: multipart/form-data

message (str)

history (JSON string) — array of { role, content }

files (0..n) — images (image/*) and PDFs (application/pdf)

Optional: model_id, quant_4bit (bool), use_cpu (bool), max_image_edge (int), max_new_tokens (int)

Response:

json
Copy code
{ "answer": "string", "usage": { "prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0 } }
POST /api/v1/chat/stream
Same fields as /chat.

SSE stream of data: <text>\n\n chunks, finished by data: [DONE]\n\n.

GET /health
Returns { "ok": true }.

Configuration (defaults)
backend/app/config.py

py
Copy code
model_id = "Qwen/Qwen2-VL-2B-Instruct"
quant_4bit = True         # set False if bitsandbytes causes issues
use_cpu = False           # set True for CPU fallback
max_image_edge = 1024     # downscale large images
max_new_tokens = 512
VRAM & Performance Tips
OOM / slow?

Set quant_4bit=False if bitsandbytes misbehaves on Windows.

Reduce max_image_edge to 768 or 640.

Lower max_new_tokens to 256–384.

Use fewer/lower-res images per request.

CPU fallback: set use_cpu=True (slower but safe).

Known Windows Tips
curl in PowerShell is an alias. Use curl.exe for -F uploads or use Invoke-RestMethod -Form (PS 7+).

Paths with spaces: prefer forward slashes: C:/Users/Your Name/…

Tech Versions (tested)
Next.js 14.2.5 • React 18.2.0 • Tailwind 3.4.4

FastAPI 0.111+ • Uvicorn 0.30+ • Transformers 4.43+ • Accelerate 0.33+

bitsandbytes 0.43+ • PyMuPDF 1.24+ • Pillow 10+

Torch (CUDA 12.1 wheels)

Troubleshooting
Streaming shows “system/user/assistant” text: fixed in services/vlm.py (streaming cleans preamble and preserves spaces). Make sure you applied the latest patch.

No styles / ugly UI: ensure app/layout.tsx imports ./globals.css.

Attachments preview missing: latest app/page.tsx includes preview grid and remove buttons.

Roadmap (optional)
Model picker (swap to larger/smaller VLMs)

Conversation history persistence (SQLite)

Settings drawer (tokens, image size, theme)

Auth for shared LAN usage

License
This repository is provided as-is for local use. No external keys required.
