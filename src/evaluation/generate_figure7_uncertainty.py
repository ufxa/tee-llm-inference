#!/usr/bin/env python3
"""Figure 7: Monte Carlo uncertainty of the trace-driven projection.
(a) CIS distribution per backend (box: 25-75th percentile, whiskers: 2.5-97.5th,
marker: midpoint of the literature range). (b) Probability of each backend
ranking (data/results/twinguard_trace_projection.json)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import figstyle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "results" / "twinguard_trace_projection.json"
OUT = ROOT / "paper" / "imagens" / "fig7-uncertainty.pdf"
NAMES = ["SGX", "TDX", "SEV-SNP"]


def main() -> None:
    figstyle.apply()
    ink = figstyle.INK
    d = json.loads(SRC.read_text())
    fig, (ra, rb) = plt.subplots(2, 1, figsize=(figstyle.COLUMN_IN, 3.3),
                                 gridspec_kw={"height_ratios": [1.0, 1.25], "hspace": 0.7})
    for i, n in enumerate(NAMES):
        q = d["backends"][n]["cis_mc_quantiles"]
        mid = d["backends"][n]["midpoint"]["cis"]
        _, _, marker = figstyle.SERIES[n]
        ra.plot([q["2.5"], q["97.5"]], [i, i], color=ink, lw=0.8)
        ra.plot([q["2.5"], q["97.5"]], [i, i], "|", color=ink, ms=6, mew=0.8)
        ra.add_patch(plt.Rectangle((q["25"], i - 0.18), q["75"] - q["25"], 0.36,
                                   facecolor=figstyle.GRAY, edgecolor=ink, lw=0.6, zorder=2))
        ra.plot(mid, i, marker, ms=5.5, mfc="white", mec=ink, mew=0.7, zorder=3)
    ra.set_yticks(range(len(NAMES)), NAMES)
    ra.set_ylim(len(NAMES) - 0.4, -0.6)
    ra.set_xlabel("CIS")
    ra.grid(axis="x"); ra.grid(axis="y", visible=False)
    ra.tick_params(axis="y", length=0)
    figstyle.panel_label(ra, "(a)", x=-0.22, y=1.04)

    ranks = list(d["ranking_probability"].items())
    labels = [k.replace("SEV-SNP", "SEV").replace(">", " > ") for k, _ in ranks]
    for y, (k, p) in enumerate(ranks):
        first = k.split(">")[0]
        face, hatch, _ = figstyle.SERIES[first]
        rb.barh(y, 100 * p, 0.62, color=face, hatch=hatch, edgecolor=ink, linewidth=0.6)
        rb.text(100 * p + 1.5, y, f"{100 * p:.1f}", va="center", fontsize=7)
    rb.set_yticks(range(len(ranks)), labels)
    rb.invert_yaxis()
    rb.set_xlim(0, 70)
    rb.set_xlabel("Probability (%)")
    rb.grid(axis="x"); rb.grid(axis="y", visible=False)
    rb.tick_params(axis="y", length=0)
    figstyle.panel_label(rb, "(b)", x=-0.22, y=1.04)
    figstyle.save(fig, OUT)
    print(f"[OK] {OUT}")


if __name__ == "__main__":
    main()
