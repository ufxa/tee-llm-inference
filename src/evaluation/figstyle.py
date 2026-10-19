"""Shared visual style for the paper figures (Figs. 4-7).

* Text in Liberation Serif (TrueType, metric-compatible with Times) to match
  the IEEE Access body font,
  8 pt at final print size (never below 7 pt).
* One neutral gray for all series; hatches, markers and line styles
  distinguish them (print- and colour-blind-safe).
* Sizes match the IEEE Access column (3.5 in) and text width (7.16 in).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

COLUMN_IN = 3.5
TEXT_IN = 7.16

_FONTS = Path("/usr/share/fonts/truetype/liberation")
for _f in ("LiberationSerif-Regular.ttf", "LiberationSerif-Bold.ttf",
           "LiberationSerif-Italic.ttf", "LiberationSerif-BoldItalic.ttf"):
    if (_FONTS / _f).exists():
        font_manager.fontManager.addfont(str(_FONTS / _f))

# Single neutral gray for every series; series are told apart by hatch
# (bars), marker (points) and line style (lines).
GRAY = "#BFBFBF"
LINE = "#4D4D4D"
# name -> (face colour, hatch, marker)
SERIES = {
    "Plaintext": (GRAY, "", "o"),
    "TLS-only":  (GRAY, "", "o"),
    "TDX":       (GRAY, "///", "o"),
    "SEV-SNP":   (GRAY, "\\\\\\", "s"),
    "SGX":       (GRAY, "xxx", "^"),
    "TwinGuard": (GRAY, "", "s"),
}
INK = "#222222"


def apply() -> None:
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
        "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
        "axes.linewidth": 0.6, "axes.edgecolor": INK, "axes.labelcolor": INK,
        "xtick.color": INK, "ytick.color": INK,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y", "axes.axisbelow": True,
        "grid.color": "#D0D0D0", "grid.linewidth": 0.5, "grid.linestyle": "-",
        "hatch.linewidth": 0.5, "hatch.color": INK,
        "legend.frameon": False, "legend.handlelength": 1.6,
        "lines.linewidth": 1.2, "lines.markersize": 4,
        "errorbar.capsize": 2.5,
        "pdf.fonttype": 42, "savefig.dpi": 600,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    })


def bar(ax, x, value, name, err=None, width=0.62, label=None):
    face, hatch, _ = SERIES[name]
    ax.bar(x, value, width, color=face, hatch=hatch, edgecolor=INK, linewidth=0.6, label=label)
    if err:
        ax.errorbar(x, value, yerr=err, fmt="none", ecolor=INK, elinewidth=0.7, capthick=0.7)


def panel_label(ax, text, x=-0.02, y=1.02):
    ax.text(x, y, text, transform=ax.transAxes, ha="left", va="bottom")


def save(fig, path) -> None:
    """Save without generator/creation-date metadata."""
    fig.savefig(path, metadata={"Creator": None, "Producer": None, "CreationDate": None})
