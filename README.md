# ValorMM — Local Multimodal Chat (Text + Images/PDFs)

**ValorMM** is a local, privacy‑first, ChatGPT‑style application you run on your own PC. It supports **normal text chat** and **multimodal Q&A** over **images and PDFs**. Attach files via a **“+” button**, **drag & drop**, or **Ctrl+V paste**. Responses are generated **entirely on your machine** (no paid APIs; no data leaves your device).

- **Frontend:** Next.js 14 · React 18 · TailwindCSS  
- **Backend:** FastAPI · Uvicorn  
- **Model:** Qwen2‑VL‑2B‑Instruct (vision‑language), optional 4‑bit quant for 4 GB VRAM  
- **Target machine:** Windows 10/11 · Ryzen 7 4800H · **RTX 3050 Ti 4 GB** · 16 GB RAM (CPU fallback available)

---

## What is ValorMM? (Description)

Most AI chat tools require API keys and upload your files to the cloud. **ValorMM** runs locally, giving you a **keyless, zero‑trust workflow** for daily work:

- Keep code, screenshots, and PDFs **offline**.
- Ask questions about **images** (UI mocks, charts, diagrams) and **documents** (invoices, specs, research PDFs) in the **same chat**.
- Use a familiar **ChatGPT‑like UI** with polished bubbles, markdown, code highlighting, **attachment previews**, and **live streaming** responses.

**You get**:  
1) A single chat box (Enter = send, Shift+Enter = newline)  
2) “+ Attach”, drag‑and‑drop, and Ctrl+V paste for files  
3) Image thumbnails & PDF chips **before sending**  
4) Streaming responses (typing effect) for text and multimodal prompts  
5) 100% local inference; models cached to your Hugging Face directory

---

## Use Cases

### Visual Q&A & Screenshot Triage
- “What does this chart say?” — summarize trends, anomalies, axes.  
- “What error is shown in this screenshot?” — extract key messages from UI/system screenshots.  
- Compare two design mocks and call out differences.

### PDF Understanding (No Cloud Uploads)
- **Invoices/Receipts:** totals, due dates, vendor names, line items.  
- **Specs/Reports:** summarize sections, extract decisions, list action items.  
- **Research PDFs:** pull out equations, datasets, or method notes.

### Developer Productivity
- Paste stack traces or attach screenshots of failing tests; ask for likely fixes.  
- Get refactors/usage with markdown code blocks in replies.  
- Brainstorm UI states using attached screenshots or component images.

### Education & Notes
- Attach textbook pages or slides; request summaries or flashcards.  
- Turn a whiteboard photo into clean notes and a study checklist.

### Privacy‑First Teams
- Handle screenshots and internal docs **locally**.  
- Useful for air‑gapped or restricted environments where cloud is not allowed.

> **Limits:** Small VLMs favor concise answers; complex visual reasoning may need larger models. OCR quality depends on image clarity. Very large/many images may need downscaling to fit 4 GB VRAM.

---

## UI Screenshots

> Replace these placeholders with your own screenshots after you run the app.

- **Chat screen** (attachments + streaming):
  
  ![Chat UI](./docs/ui-chat.png)

---

## Installation (Windows‑first)

### 1) Backend (FastAPI, port 8000)

```powershell
# From repo root
cd .\backend\
python -m venv .venv
. .\.venv\Scripts\Activate
python -m pip install --upgrade pip

# PyTorch CUDA 12.1 (RTX 30‑series)
pip install --index-url https://download.pytorch.org/whl/cu121 torch torchvision torchaudio

# App deps
pip install -r requirements.txt

# Start API
.\run_dev.ps1
# -> http://127.0.0.1:8000  (health: /health)
```

**Quick test (text):**
```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/chat" -F "message=Hello!"
```

**Quick test (image upload):**
```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/chat" ^
  --form "message=What is in this picture?" ^
  --form "files=@"C:/path/to/photo.jpg";type=image/jpeg"
```

### 2) Frontend (Next.js, port 3000)

```powershell
# New terminal
cd .\frontend\
npm install
npm run dev
# -> http://localhost:3000
```

**Usage:**  
- Type → **Enter** to send; **Shift+Enter** for a newline  
- **+** to attach files, **drag & drop**, or **Ctrl+V** paste  
- Preview thumbnails (images) and chips (PDFs) before sending  
- Get **streaming** replies like ChatGPT

---

## Performance & Tuning (Guidance)

Below are **illustrative** measurements to guide your settings on an RTX 3050 Ti 4 GB with Qwen2‑VL‑2B. Actual results vary by driver, background apps, and content.

- **Reduce latency** by lowering `max_new_tokens` or `max_image_edge`.  
- **Prevent OOM** by setting `quant_4bit=True` (default) and `max_image_edge` to **768** or **640** for large images.  
- **CPU fallback:** set `use_cpu=True` (much slower, but safe).

**Latency vs max_new_tokens**  
![Latency vs tokens](./docs/perf-latency-vs-tokens.png)

**Latency vs image size**  
![Latency vs image size](./docs/perf-latency-vs-imageedge.png)

**Approx. VRAM vs image size (4‑bit)**  
![VRAM vs image size](./docs/perf-vram-vs-imageedge.png)

---

## Troubleshooting

- **Weird “system/user/assistant” text shows up** — ensure you applied the latest backend streaming patch; ValorMM strips the chat preamble and preserves spaces.  
- **No styles / ugly UI** — make sure `app/layout.tsx` imports `./globals.css`.  
- **Uploads not visible before sending** — latest `page.tsx` shows previews with remove buttons.  
- **curl errors in PowerShell** — use `curl.exe` (not the alias), or `Invoke-RestMethod -Form` in PS 7+.

---

## Roadmap (optional)

- Model picker (swap VLMs)  
- Conversation history persistence (SQLite)  
- Settings drawer (tokens, image size, theme)  
- Auth for shared LAN usage
