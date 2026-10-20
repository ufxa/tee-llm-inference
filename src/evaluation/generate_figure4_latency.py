#!/usr/bin/env python3
"""Figure 4: measured RTX 5090 latency and trace-driven TEE projections.

Bars: mean latency over the 1.2 M measured requests (baseline) and projected
mean latency per backend at the midpoint of the literature overhead range;
whiskers span the low and high ends of that range
(data/results/twinguard_trace_projection.json)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import figstyle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "results" / "twinguard_trace_projection.json"
OUT = ROOT / "paper" / "imagens" / "fig4-latency.pdf"


def main() -> None:
    figstyle.apply()
    d = json.loads(SRC.read_text())
    base = d["trace"]["measured_latency_mean_ms"]
    items = [("Plaintext", "Measured\n(no TEE)", base, base, base)]
    for b, label in (("SEV-SNP", "TG-SEV"), ("TDX", "TG-TDX"), ("SGX", "TG-SGX")):
        r = d["backends"][b]
        items.append((b, label, r["midpoint"]["latency_mean_ms"],
                      r["low_end"]["latency_mean_ms"], r["high_end"]["latency_mean_ms"]))
    fig, ax = plt.subplots(figsize=(figstyle.COLUMN_IN, 2.15))
    for i, (name, label, mid, lo, hi) in enumerate(items):
        _, _, marker = figstyle.SERIES[name]
        ax.errorbar(i, mid, yerr=[[mid - lo], [hi - mid]] if hi > lo else None, fmt=marker, ms=5.5,
                    mfc="white" if i == 0 else figstyle.GRAY, mec=figstyle.INK, mew=0.7,
                    ecolor=figstyle.INK, elinewidth=0.8, capsize=3)
        ax.text(i + 0.12, mid, f"{mid:.0f}", ha="left", va="center", fontsize=7.5)
    ax.set_xticks(range(len(items)), [it[1] for it in items])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("Mean latency (ms)")
    ax.set_ylim(1100, 1340)
    ax.set_xlim(-0.5, len(items) - 0.4)
    figstyle.save(fig, OUT)
    print(f"[OK] {OUT}")


if __name__ == "__main__":
    main()
