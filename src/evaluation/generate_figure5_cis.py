#!/usr/bin/env python3
"""Figure 5: CIS of the reference systems and the trace-driven TwinGuard
projections. (a) Full scale; baselines follow Eq. (1) directly.
(b) TwinGuard backends: midpoint and 95% Monte Carlo interval over the
literature overhead ranges (data/results/twinguard_trace_projection.json)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import figstyle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "results" / "twinguard_trace_projection.json"
OUT = ROOT / "paper" / "imagens" / "fig5-cis.pdf"
THRESHOLD = 0.90
TG = [("SEV-SNP", "TG-SEV"), ("TDX", "TG-TDX"), ("SGX", "TG-SGX")]


def main() -> None:
    figstyle.apply()
    d = json.loads(SRC.read_text())
    fig, (a, b) = plt.subplots(1, 2, figsize=(figstyle.COLUMN_IN, 2.25),
                               gridspec_kw={"width_ratios": [1.6, 1.0], "wspace": 0.38})
    items = [("Plaintext", "Plaintext", d["baselines"]["Plaintext"]["cis"]),
             ("TLS-only", "TLS-only", d["baselines"]["TLS-only"]["cis"])]
    items += [(b_, lab, d["backends"][b_]["midpoint"]["cis"]) for b_, lab in TG]
    for i, (name, label, v) in enumerate(items):
        figstyle.bar(a, i, v, name)
        if i < 2:
            a.text(i, v + 0.02, f"{v:.3f}", ha="center", va="bottom", fontsize=7)
    a.axhline(THRESHOLD, color=figstyle.INK, lw=0.7, ls=(0, (4, 2)))
    a.set_xticks(range(len(items)), [it[1] for it in items], rotation=35, ha="right", rotation_mode="anchor")
    a.tick_params(axis="x", length=0)
    a.set_ylabel("CIS")
    a.set_ylim(0, 1.05)
    figstyle.panel_label(a, "(a)")

    for i, (name, label) in enumerate(TG):
        r = d["backends"][name]
        mid = r["midpoint"]["cis"]
        lo, hi = r["cis_mc_ci95"]
        _, _, marker = figstyle.SERIES[name]
        b.errorbar(i, mid, yerr=[[mid - lo], [hi - mid]], fmt=marker, ms=5, mfc=figstyle.GRAY,
                   mec=figstyle.INK, mew=0.6, ecolor=figstyle.INK, elinewidth=0.8, capsize=3)
    b.axhline(THRESHOLD, color=figstyle.INK, lw=0.7, ls=(0, (4, 2)))
    b.set_xlim(-0.6, 2.6)
    b.set_ylim(0.895, 0.94)
    b.set_yticks([0.90, 0.91, 0.92, 0.93, 0.94])
    b.set_xticks(range(3), ["SEV", "TDX", "SGX"])
    b.tick_params(axis="x", length=0)
    figstyle.panel_label(b, "(b)")
    figstyle.save(fig, OUT)
    print(f"[OK] {OUT}")


if __name__ == "__main__":
    main()
