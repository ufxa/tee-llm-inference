#!/usr/bin/env python3
"""Generate Figure 6 from the measured RTX 5090 calibration (concurrency 1--16):
(a) throughput, (b) mean and p95 latency. Measured data only."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PHYSICAL_CSV = ROOT / "data" / "results" / "rtx5090_calibration_scalability.csv"
PDF_OUTPUT = ROOT / "paper" / "imagens" / "fig6-calibration.pdf"


def read_csv(path: Path) -> list[dict[str, float | str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    import matplotlib.pyplot as plt

    physical = read_csv(PHYSICAL_CSV)
    expected_physical = [1, 2, 4, 8, 16]
    actual_physical = [int(row["concurrency"]) for row in physical]
    if actual_physical != expected_physical:
        raise ValueError(f"unexpected physical concurrencies: {actual_physical}")
    if any(float(row["success_rate"]) != 1.0 for row in physical):
        raise ValueError("physical calibration must contain only successful runs")

    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import figstyle
    figstyle.apply()
    ink = figstyle.INK
    fig, (tp_ax, lat_ax) = plt.subplots(
        1, 2, figsize=(figstyle.COLUMN_IN, 1.85), gridspec_kw={"wspace": 0.55})

    x = [int(row["concurrency"]) for row in physical]
    throughput = [float(row["requests_per_second"]) for row in physical]
    mean_lat = [float(row["mean_latency_ms"]) for row in physical]
    p95 = [float(row["p95_latency_ms"]) for row in physical]
    for ax in (tp_ax, lat_ax):
        ax.set_xscale("log", base=2)
        ax.set_xticks(x, [str(v) for v in x])
        ax.minorticks_off()
        ax.set_xlabel("Concurrent clients")
        ax.grid(axis="both")
    tp_ax.plot(x, throughput, color=figstyle.LINE, marker="o", mfc=figstyle.GRAY, mec=ink, mew=0.5)
    tp_ax.set_ylabel("Throughput (req/s)")
    tp_ax.set_ylim(0, 16)
    figstyle.panel_label(tp_ax, "(a)")

    lat_ax.plot(x, p95, color=figstyle.LINE, marker="s", mfc=figstyle.GRAY, mec=ink, mew=0.5,
                label="p95")
    lat_ax.plot(x, mean_lat, color=figstyle.LINE, marker="o", mfc="white", mec=ink, mew=0.5, ls=(0, (3, 2)), label="mean")
    lat_ax.set_ylabel("Latency (ms)")
    lat_ax.set_ylim(400, 1400)
    lat_ax.legend(loc="upper left", labels=["p95", "Mean"])
    figstyle.panel_label(lat_ax, "(b)")

    PDF_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figstyle.save(fig, PDF_OUTPUT)
    plt.close(fig)
    print(f"[OK] wrote {PDF_OUTPUT}")


if __name__ == "__main__":
    main()
