# ValorMM Bench — How to Produce Real Performance Graphs

This kit lets you run **real benchmarks** on your machine and generate graphs for your README.

## 1) (Optional but recommended) Backend metrics patch for GPU VRAM

Add peak VRAM to the `/api/v1/chat` response. Edit `backend/app/services/vlm.py` `chat_once()`:

```py
import torch

def chat_once(...):
    from qwen_vl_utils import process_vision_info
    model, processor = get_model(...)

    # reset peak stats before generation
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    # ... existing code before generate()

    t0 = time.time()
    with torch.no_grad():
        outputs = model.generate(...)

    latency_ms = int((time.time() - t0) * 1000)

    # NEW: capture peak memory (in MB)
    peak_vram_mb = 0
    if torch.cuda.is_available():
        try:
            peak_vram_mb = int(torch.cuda.max_memory_reserved() / (1024*1024))
        except Exception:
            pass

    # ... decode text, compute tokens ...

    usage = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_ms": latency_ms,
        "peak_vram_mb": peak_vram_mb,   # <-- add here
    }
    return text, usage
```

Also add the field to `backend/app/schemas.py`:

```py
class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    peak_vram_mb: int | None = None   # <-- add this
```

Restart the API.

> If you skip this patch, the **VRAM plot** will be skipped. Latency plots will still work.

## 2) Run the benchmark

Open a terminal in the repo root and run:

```bash
cd ValorMM-Bench
python bench.py --server http://127.0.0.1:8000 --image C:/path/to/your.jpg --rounds 3
# or for PDF:
# python bench.py --server http://127.0.0.1:8000 --pdf C:/path/to/file.pdf --rounds 3
```

Options you can tweak:
- `--tokens 128 256 384 512`  → max_new_tokens sweep
- `--edges 640 768 1024`      → max_image_edge sweep
- `--quant_4bit true|false`
- `--use_cpu true|false`
- `--message "Describe this content."`
- `--rounds 3` (repeat per combo)

Results go to: `ValorMM-Bench/bench_out/results.csv`

## 3) Make graphs

```bash
python plot_results.py
```
This writes PNGs under `ValorMM-Bench/docs/`:
- `perf-latency-vs-tokens.png`
- `perf-latency-vs-imageedge.png`
- `perf-vram-vs-imageedge.png` (only if backend provides `peak_vram_mb`)

## 4) Update your README

Copy the generated graphs into your repo `docs/` folder (or update paths), and adjust your README to point at your **real** results.

## Notes

- Prefer testing with a **representative image/PDF** from your use case.
- For consistent results, **close other GPU apps**, and run each test twice (ignore first warm-up round).
- CPU fallback works, but is much slower; use it only if you need a CPU-only baseline.
