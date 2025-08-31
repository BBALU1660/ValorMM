#!/usr/bin/env python3
"""
ValorMM Benchmark Runner
- Measures end-to-end HTTP latency and model latency from API response
- Optionally captures peak_vram_mb if backend exposes it
- Saves CSV to bench_out/results.csv
Usage (examples):
  python bench.py --server http://127.0.0.1:8000 --image C:\path\img.jpg --rounds 3
  python bench.py --server http://127.0.0.1:8000 --pdf C:\path\file.pdf --tokens 128 256 384 512 --edges 640 768 1024
"""
import argparse, csv, os, time, datetime as dt, requests

def as_bool(x: str) -> bool:
    s = str(x).lower()
    return s in ("1","true","yes","y","on")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8000", help="ValorMM backend base URL")
    ap.add_argument("--image", help="Path to an image file to test")
    ap.add_argument("--pdf", help="Path to a PDF file to test")
    ap.add_argument("--rounds", type=int, default=3, help="Repetitions per configuration")
    ap.add_argument("--tokens", type=int, nargs="*", default=[128,256,384,512], help="List of max_new_tokens to test")
    ap.add_argument("--edges", type=int, nargs="*", default=[640,768,896,1024], help="List of max_image_edge to test")
    ap.add_argument("--quant_4bit", type=as_bool, default=True, help="Use 4-bit quantization (True/False)")
    ap.add_argument("--use_cpu", type=as_bool, default=False, help="Force CPU usage (True/False)")
    ap.add_argument("--message", default="Briefly describe this content.", help="Prompt message to use")
    ap.add_argument("--model_id", default="Qwen/Qwen2-VL-2B-Instruct", help="HF model id")
    args = ap.parse_args()

    os.makedirs("bench_out", exist_ok=True)
    csv_path = os.path.join("bench_out", "results.csv")
    fieldnames = [
        "timestamp","server","model_id","quant_4bit","use_cpu","max_image_edge","max_new_tokens",
        "files","http_ms","model_latency_ms","peak_vram_mb","answer_chars","status"
    ]
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=fieldnames).writeheader()

    files_payload = []
    files_desc = []
    if args.image and os.path.exists(args.image):
        files_payload.append(("files", (os.path.basename(args.image), open(args.image, "rb"), "image/jpeg")))
        files_desc.append(os.path.basename(args.image))
    if args.pdf and os.path.exists(args.pdf):
        files_payload.append(("files", (os.path.basename(args.pdf), open(args.pdf, "rb"), "application/pdf")))
        files_desc.append(os.path.basename(args.pdf))

    target = args.server.rstrip("/") + "/api/v1/chat"

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for edge in args.edges:
            for toks in args.tokens:
                for r in range(args.rounds):
                    form = {
                        "message": args.message,
                        "history": "[]",
                        "model_id": args.model_id,
                        "quant_4bit": str(bool(args.quant_4bit)).lower(),
                        "use_cpu": str(bool(args.use_cpu)).lower(),
                        "max_image_edge": str(int(edge)),
                        "max_new_tokens": str(int(toks)),
                    }
                    t0 = time.perf_counter()
                    try:
                        resp = requests.post(target, data=form, files=files_payload if files_payload else None, timeout=600)
                        http_ms = int((time.perf_counter() - t0)*1000)
                        status = resp.status_code
                        peak_vram = ""
                        model_ms = ""
                        answer_chars = ""
                        if status == 200:
                            data = resp.json()
                            answer = data.get("answer","")
                            usage = data.get("usage",{})
                            model_ms = usage.get("latency_ms","")
                            # Accept either nested or top-level
                            peak_vram = usage.get("peak_vram_mb","") or data.get("peak_vram_mb","")
                            answer_chars = len(str(answer))
                        else:
                            try:
                                data = resp.json()
                                answer_chars = len(str(data))
                            except Exception:
                                answer_chars = 0
                        writer.writerow({
                            "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
                            "server": args.server,
                            "model_id": args.model_id,
                            "quant_4bit": args.quant_4bit,
                            "use_cpu": args.use_cpu,
                            "max_image_edge": edge,
                            "max_new_tokens": toks,
                            "files": ";".join(files_desc) if files_desc else "none",
                            "http_ms": http_ms,
                            "model_latency_ms": model_ms,
                            "peak_vram_mb": peak_vram,
                            "answer_chars": answer_chars,
                            "status": status
                        })
                        print(f"[OK] edge={edge} toks={toks} r={r+1}/{args.rounds} http_ms={http_ms} model_ms={model_ms} vram={peak_vram}")
                    except Exception as e:
                        http_ms = int((time.perf_counter() - t0)*1000)
                        writer.writerow({
                            "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
                            "server": args.server,
                            "model_id": args.model_id,
                            "quant_4bit": args.quant_4bit,
                            "use_cpu": args.use_cpu,
                            "max_image_edge": edge,
                            "max_new_tokens": toks,
                            "files": ";".join(files_desc) if files_desc else "none",
                            "http_ms": http_ms,
                            "model_latency_ms": "",
                            "peak_vram_mb": "",
                            "answer_chars": "",
                            "status": f"error:{e}"
                        })
                        print(f"[ERR] edge={edge} toks={toks} r={r+1}/{args.rounds} error={e}")
    print(f"\nSaved CSV: {csv_path}")
if __name__ == "__main__":
    main()
