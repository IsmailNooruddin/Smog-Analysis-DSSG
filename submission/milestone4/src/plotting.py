"""One figure style for every Milestone 2 figure (merge_analysis.ipynb).

Rules we follow on every figure (Grammar of Graphics checklist from the rubric):
- an informative title, axes with physical units, a legend whenever there are 2+ series;
- colorblind-safe colours: Okabe-Ito for categories (fixed order, checked with a
  colour-vision-deficiency validator), one-hue 'cividis' for magnitudes, and the
  two-hue 'RdBu_r' with a grey-white midpoint for signed values such as correlations;
- the same font sizes, grid and export settings (300 dpi PNG in figures/).
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# Okabe-Ito colours in a fixed order (adjacent pairs pass the CVD check in this order).
# A category always keeps its colour; we never cycle or re-rank colours.
CAT_COLORS = ["#0072B2", "#D55E00", "#009E73", "#E69F00", "#CC79A7", "#56B4E9"]
GREY = "#6E6E6E"
SEQ_CMAP = "cividis"     # magnitude (one hue family, light to dark)
DIV_CMAP = "RdBu_r"      # signed values: blue = negative, red = positive, white = 0

# Fixed colours for the groups that appear in several figures
GROUP_COLORS = {
    "Near border (PK)": CAT_COLORS[0],
    "Intermediate (PK)": CAT_COLORS[3],
    "Far (PK)": CAT_COLORS[2],
    "Indian Punjab": CAT_COLORS[1],
}
ORIGIN_COLORS = {"IN": CAT_COLORS[1], "PK": CAT_COLORS[0]}


def set_style():
    """Apply the shared style. Call once at the top of the notebook."""
    mpl.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#E5E5E5",
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "lines.linewidth": 2,
        "axes.prop_cycle": mpl.cycler(color=CAT_COLORS),
    })


def save(fig, name, fig_dir="figures"):
    """Save a figure as figures/<name>.png (300 dpi) and return the path."""
    path = Path(fig_dir) / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    return path
