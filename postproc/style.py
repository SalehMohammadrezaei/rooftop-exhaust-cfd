"""One figure style for the whole project. Import and call use() before plotting.

Palette and sizes are fixed here so every figure in results/ and the README looks the same.
Colour maps are the Crameri scientific maps (perceptually uniform, print-safe): batlow for
velocity, davos (reversed) for concentration, vik for signed differences.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt

INK = "#1b1f24"        # text, axes, measured data
GREY = "#7a818c"       # secondary lines, reference bands
LIGHT = "#d6dae0"      # grid, fills
CFD = "#1f6f8b"        # simulation, primary
CFD2 = "#c98b2a"       # second simulation variant
CFD3 = "#b5443c"       # third variant / limit lines
CFD4 = "#5b8c5a"       # fourth variant
SERIES = [CFD, CFD2, CFD3, CFD4, GREY]

FULL = 6.3             # inch, text width of an A4 report
HALF = 3.1

def cmap(name):
    import cmcrameri.cm as cmc
    return {"vel": cmc.batlow, "conc": cmc.davos_r, "diff": cmc.vik, "seq": cmc.lapaz_r}[name]

def use():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Nimbus Sans", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9, "legend.fontsize": 8,
        "xtick.labelsize": 8, "ytick.labelsize": 8,
        "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK, "ytick.color": INK,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.7, "xtick.major.width": 0.7, "ytick.major.width": 0.7,
        "xtick.direction": "out", "ytick.direction": "out",
        "axes.grid": False,
        "legend.frameon": False, "legend.handlelength": 1.8,
        "lines.linewidth": 1.3, "lines.markersize": 4,
        "figure.dpi": 110, "savefig.dpi": 220, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
        "axes.titlelocation": "left", "axes.titleweight": "normal",
        "axes.formatter.use_mathtext": True,
    })

def save(fig, path):
    """PNG for the README, PDF for a report; same basename."""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path if path.endswith(".png") else path + ".png")
    fig.savefig((path[:-4] if path.endswith(".png") else path) + ".pdf")
    plt.close(fig)

def panel_label(ax, s):
    ax.text(0.0, 1.02, s, transform=ax.transAxes, ha="left", va="bottom", fontweight="bold")
