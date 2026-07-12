from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


OUTPUT_DIR = Path(__file__).resolve().parent / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DPI = 300
BG = "#f7f7f5"
TEXT = "#1f2933"
GRID = "#d6d6d1"
RED = "#b23a48"
DARK_RED = "#7f1d1d"
BLUE = "#2b6cb0"
GREEN = "#2f855a"
GRAY = "#9aa5b1"
CHARCOAL = "#364152"
LIGHT_GREEN = "#c6f6d5"
LIGHT_RED = "#fed7d7"


def setup_style() -> None:
    sns.set_theme(
        style="whitegrid",
        context="talk",
        rc={
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "axes.edgecolor": "#a8a8a2",
            "axes.labelcolor": TEXT,
            "axes.titlecolor": TEXT,
            "axes.titlesize": 18,
            "axes.labelsize": 13,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "grid.alpha": 0.65,
            "savefig.facecolor": BG,
            "savefig.bbox": "tight",
            "font.family": "DejaVu Sans",
        },
    )


def clean_axes(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#a8a8a2")
    ax.spines["bottom"].set_color("#a8a8a2")


def fmt_dollar(value: float) -> str:
    return f"-${abs(value):,.2f}" if value < 0 else f"${value:,.2f}"


def chart_1_trade_economics() -> None:
    labels = ["Gross Market Loss", "Commission Costs", "Total Net Loss"]
    gross_loss = -1.63
    commission = -41.12
    total = -42.75

    starts = np.array([0.0, gross_loss, 0.0])
    heights = np.array([gross_loss, commission, total])
    colors = [RED, DARK_RED, CHARCOAL]

    fig, ax = plt.subplots(figsize=(10, 7))
    x = np.arange(len(labels))
    width = 0.62

    for i, (start, height, color) in enumerate(zip(starts, heights, colors)):
        ax.bar(x[i], height, bottom=start if i == 1 else 0, width=width, color=color, edgecolor="none")

    ax.plot([x[0], x[1]], [gross_loss, gross_loss], color="#6b7280", lw=1.5, ls="--", alpha=0.8)
    ax.axhline(0, color="#6b7280", lw=1.2)

    for i, value in enumerate([gross_loss, commission, total]):
        if i == 1:
            y = gross_loss + commission / 2
        else:
            y = value / 2
        ax.text(
            x[i],
            y,
            fmt_dollar(value),
            ha="center",
            va="center",
            color="white",
            fontsize=12,
            fontweight="bold",
        )

    ax.set_title("The Economics of a Trade")
    ax.set_ylabel("Per-Lot P&L")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(-48, 6)
    ax.text(
        1,
        2.2,
        "Median trader loss is driven mainly by commissions",
        ha="center",
        va="bottom",
        color=TEXT,
        fontsize=11,
    )
    clean_axes(ax)
    fig.savefig(OUTPUT_DIR / "chart_1_trade_economics.png", dpi=DPI)
    plt.close(fig)


def chart_2_c53_shift() -> None:
    eras = ["Prelude Era\n(C33-C52)", "Primary Era\n(C53-C65)"]
    activation = [6.5, 34.0]
    sl_usage = [98.5, 76.1]
    colors = [BLUE, GREEN]

    fig, axes = plt.subplots(1, 2, figsize=(13, 6.5), sharey=True)
    metrics = [
        ("Activation Rate", activation, "% of Registrants Who Trade"),
        ("Stop-Loss Usage", sl_usage, "% of Positions With SL Set"),
    ]

    for ax, (title, values, ylabel) in zip(axes, metrics):
        bars = ax.bar(eras, values, color=colors, width=0.58, edgecolor="none")
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, 105)
        ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0f}%")
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + 2.2,
                f"{value:.1f}%",
                ha="center",
                va="bottom",
                fontsize=12,
                color=TEXT,
                fontweight="bold",
            )
        clean_axes(ax)

    fig.suptitle("The C53 Shift: Platform Behavior Before vs. After", y=1.02, fontsize=18, color=TEXT)
    fig.savefig(OUTPUT_DIR / "chart_2_c53_shift.png", dpi=DPI)
    plt.close(fig)


def chart_3_fade_triggers() -> None:
    triggers = [
        "Small Size + Streak >= 2",
        "Loss Streak >= 2",
        "Loss Streak >= 3",
        "Late + Underwater",
        "Base Rate",
    ]
    point = np.array([114.84, 40.54, 37.47, 21.45, 12.44])
    lower = np.array([32.47, 11.36, np.nan, np.nan, np.nan])
    upper = np.array([198.33, 70.21, np.nan, np.nan, np.nan])
    hurdle = 7.00

    colors = [
        BLUE if not np.isnan(lo) and lo > hurdle else GRAY
        for lo in lower
    ]

    y = np.arange(len(triggers))
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.barh(y, point, color=colors, edgecolor="none", height=0.68)

    for idx, (mu, lo, hi) in enumerate(zip(point, lower, upper)):
        if not np.isnan(lo):
            ax.errorbar(
                x=mu,
                y=idx,
                xerr=np.array([[mu - lo], [hi - mu]]),
                fmt="none",
                ecolor=CHARCOAL,
                elinewidth=2,
                capsize=5,
                capthick=2,
            )
        label = f"${mu:.2f}"
        if not np.isnan(lo):
            label += f"  [{lo:.2f}, {hi:.2f}]"
        ax.text(mu + 3.5, idx, label, va="center", ha="left", fontsize=11, color=TEXT)

    ax.axvline(hurdle, color=RED, lw=2.5, ls="--")
    ax.annotate(
        "C22 Cost Hurdle ($7.00)",
        xy=(hurdle, 3.8),
        xytext=(24, 4.35),
        arrowprops=dict(arrowstyle="->", color=RED, lw=1.8),
        color=RED,
        fontsize=11,
        fontweight="bold",
    )

    ax.set_title("Asymmetric Fade Triggers With Confidence Intervals")
    ax.set_xlabel("Expected Gross Loss Per Lot")
    ax.set_yticks(y)
    ax.set_yticklabels(triggers)
    ax.set_xlim(0, 215)
    ax.invert_yaxis()
    clean_axes(ax)
    fig.savefig(OUTPUT_DIR / "chart_3_fade_triggers.png", dpi=DPI)
    plt.close(fig)


def chart_4_sizing_paradox() -> None:
    quartiles = ["Q1\n(Smallest)", "Q2", "Q3", "Q4\n(Largest)"]
    values = np.array([114.84, 28.69, 10.02, -2.68])
    hurdle = 7.00
    x = np.arange(len(quartiles))

    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    ax.plot(
        x,
        values,
        color=BLUE,
        lw=3,
        marker="o",
        markersize=9,
        markerfacecolor="white",
        markeredgewidth=2.5,
    )
    ax.axhline(hurdle, color=RED, lw=2.5, ls="--")

    ax.fill_between(x, values, hurdle, where=values >= hurdle, interpolate=True, color=LIGHT_GREEN, alpha=0.8)
    ax.fill_between(x, values, hurdle, where=values < hurdle, interpolate=True, color=LIGHT_RED, alpha=0.85)

    for xi, yi in zip(x, values):
        ax.text(
            xi,
            yi + (5 if yi >= hurdle else -7),
            f"${yi:.2f}",
            ha="center",
            va="bottom" if yi >= hurdle else "top",
            fontsize=11,
            color=TEXT,
            fontweight="bold",
        )

    ax.annotate(
        "Fading Breakeven Hurdle",
        xy=(2.65, hurdle),
        xytext=(1.55, 26),
        arrowprops=dict(arrowstyle="->", color=RED, lw=1.8),
        color=RED,
        fontsize=11,
        fontweight="bold",
    )

    ax.set_title("The Sizing Paradox Within the Confirmed Trigger")
    ax.set_xlabel("Trade Size Quartile")
    ax.set_ylabel("Expected Gross Loss Per Lot")
    ax.set_xticks(x)
    ax.set_xticklabels(quartiles)
    ax.set_ylim(-15, 130)
    clean_axes(ax)
    fig.savefig(OUTPUT_DIR / "chart_4_sizing_paradox.png", dpi=DPI)
    plt.close(fig)


def main() -> None:
    setup_style()
    chart_1_trade_economics()
    chart_2_c53_shift()
    chart_3_fade_triggers()
    chart_4_sizing_paradox()
    print(f"Saved charts to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
