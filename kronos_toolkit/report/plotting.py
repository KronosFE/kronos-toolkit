"""Brand-consistent plotting — KFE design system.

Flat, honest, no gradients / glows / teal. Matplotlib if available; the module
imports cleanly even when it is not (functions raise only when actually called).
Colors and type follow the Kronos publication palette.
"""

# KFE publication palette (no teal, no neon).
KFE_INK = "#14171A"
KFE_PAPER = "#FBFAF7"
KFE_BREEDER = "#1F4E79"      # deep blue — breeder
KFE_BURNER = "#B5651D"       # burnt amber — burner
KFE_ACCENT = "#6E5AA6"       # muted violet — accent
KFE_MUTED = "#8A8A82"        # gray — neutral / structural
KFE_GO = "#2E7D46"
KFE_NOGO = "#A32D2D"
KFE_COND = "#B08900"

CYCLE = [KFE_BREEDER, KFE_BURNER, KFE_ACCENT, KFE_MUTED]


def _mpl():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except Exception as e:
        raise RuntimeError(
            "matplotlib is required for plotting; install it or use tables/CSV") from e


def apply_style(plt):
    plt.rcParams.update({
        "figure.facecolor": KFE_PAPER,
        "axes.facecolor": KFE_PAPER,
        "axes.edgecolor": KFE_INK,
        "axes.labelcolor": KFE_INK,
        "text.color": KFE_INK,
        "xtick.color": KFE_INK,
        "ytick.color": KFE_INK,
        "axes.grid": True,
        "grid.color": "#E3E1DA",
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 11,
        "axes.prop_cycle": plt.cycler(color=CYCLE),
    })


def line_plot(x, series, xlabel="", ylabel="", title="", path=None,
              markers=None, hlines=None):
    """Flat brand line plot. series = {label: y-values}. Saves to path if given."""
    plt = _mpl()
    apply_style(plt)
    fig, ax = plt.subplots(figsize=(7, 4.3))
    for i, (label, y) in enumerate(series.items()):
        ax.plot(x, y, label=label, lw=2.0,
                marker=(markers or {}).get(label))
    for hy in (hlines or []):
        ax.axhline(hy["y"], color=hy.get("color", KFE_MUTED),
                   ls="--", lw=1.2, label=hy.get("label"))
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title, loc="left", fontweight="medium")
    if len(series) > 1 or hlines:
        ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150, facecolor=KFE_PAPER)
        plt.close(fig)
        return path
    return fig


def gate_bar(gates, path=None, title="Gate status"):
    """Horizontal status bars. gates = [{name, status in {GO,NO-GO,CONDITIONAL}}]."""
    plt = _mpl()
    apply_style(plt)
    color = {"GO": KFE_GO, "NO-GO": KFE_NOGO, "CONDITIONAL": KFE_COND}
    fig, ax = plt.subplots(figsize=(7, 0.5 * len(gates) + 1.2))
    for i, g in enumerate(reversed(gates)):
        ax.barh(i, 1.0, color=color.get(g["status"], KFE_MUTED), height=0.6)
        ax.text(0.02, i, g["name"], va="center", ha="left",
                color=KFE_PAPER, fontsize=10)
        ax.text(0.98, i, g["status"], va="center", ha="right",
                color=KFE_PAPER, fontsize=9, fontweight="medium")
    ax.set_xlim(0, 1); ax.set_yticks([]); ax.set_xticks([])
    ax.set_title(title, loc="left", fontweight="medium")
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150, facecolor=KFE_PAPER)
        plt.close(fig)
        return path
    return fig
