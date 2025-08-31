#!/usr/bin/env python3
"""
Plot ValorMM Bench results (bench_out/results.csv) to PNGs under docs/
"""
import csv, os
from collections import defaultdict
import matplotlib.pyplot as plt

CSV_PATH = os.path.join("bench_out", "results.csv")
DOCS_DIR = "docs"

def load_rows():
    rows = []
    if not os.path.exists(CSV_PATH):
        print("No results.csv found. Run bench.py first.")
        return rows
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                row["max_image_edge"] = int(row["max_image_edge"])
                row["max_new_tokens"] = int(row["max_new_tokens"])
                row["http_ms"] = int(row["http_ms"])
                row["model_latency_ms"] = int(row["model_latency_ms"]) if row["model_latency_ms"] != "" else None
                row["peak_vram_mb"] = int(float(row["peak_vram_mb"])) if row["peak_vram_mb"] not in ("", None) else None
                rows.append(row)
            except Exception:
                pass
    return rows

def plot_latency_vs_tokens(rows):
    # Group by edge; use mean http_ms
    data = defaultdict(list)
    for r in rows:
        key = r["max_image_edge"]
        data[key].append(r)
    plt.figure(figsize=(7,4))
    for edge, items in sorted(data.items()):
        by_tok = defaultdict(list)
        for it in items:
            by_tok[it["max_new_tokens"]].append(it["http_ms"])
        xs, ys = [], []
        for tok, vals in sorted(by_tok.items()):
            xs.append(tok)
            ys.append(sum(vals)/len(vals))
        plt.plot(xs, ys, marker="o", label=f"edge={edge}")
    plt.title("Latency (HTTP) vs max_new_tokens")
    plt.xlabel("max_new_tokens")
    plt.ylabel("End-to-end latency (ms)")
    plt.legend()
    os.makedirs(DOCS_DIR, exist_ok=True)
    out = os.path.join(DOCS_DIR, "perf-latency-vs-tokens.png")
    plt.savefig(out, bbox_inches="tight", dpi=160)
    print("Saved", out)

def plot_latency_vs_edge(rows):
    # Group by tokens; use mean http_ms
    data = defaultdict(list)
    for r in rows:
        key = r["max_new_tokens"]
        data[key].append(r)
    plt.figure(figsize=(7,4))
    for toks, items in sorted(data.items()):
        by_edge = defaultdict(list)
        for it in items:
            by_edge[it["max_image_edge"]].append(it["http_ms"])
        xs, ys = [], []
        for edge, vals in sorted(by_edge.items()):
            xs.append(edge)
            ys.append(sum(vals)/len(vals))
        plt.plot(xs, ys, marker="o", label=f"tokens={toks}")
    plt.title("Latency (HTTP) vs max_image_edge")
    plt.xlabel("max_image_edge (px)")
    plt.ylabel("End-to-end latency (ms)")
    plt.legend()
    os.makedirs(DOCS_DIR, exist_ok=True)
    out = os.path.join(DOCS_DIR, "perf-latency-vs-imageedge.png")
    plt.savefig(out, bbox_inches="tight", dpi=160)
    print("Saved", out)

def plot_vram_vs_edge(rows):
    # Use peak_vram_mb if present
    by_edge = defaultdict(list)
    for r in rows:
        if r["peak_vram_mb"] is not None:
            by_edge[r["max_image_edge"]].append(r["peak_vram_mb"])
    if not by_edge:
        print("No peak_vram_mb found. Apply backend metrics patch or ignore this plot.")
        return
    plt.figure(figsize=(7,4))
    xs, ys = [], []
    for edge, vals in sorted(by_edge.items()):
        xs.append(edge)
        ys.append(sum(vals)/len(vals))
    plt.plot(xs, ys, marker="o")
    plt.title("Approx. Peak VRAM vs max_image_edge")
    plt.xlabel("max_image_edge (px)")
    plt.ylabel("Peak VRAM (MB)")
    os.makedirs(DOCS_DIR, exist_ok=True)
    out = os.path.join(DOCS_DIR, "perf-vram-vs-imageedge.png")
    plt.savefig(out, bbox_inches="tight", dpi=160)
    print("Saved", out)

def main():
    rows = load_rows()
    if not rows:
        return
    plot_latency_vs_tokens(rows)
    plot_latency_vs_edge(rows)
    plot_vram_vs_edge(rows)
if __name__ == "__main__":
    main()
