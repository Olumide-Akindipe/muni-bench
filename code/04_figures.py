#!/usr/bin/env python3
"""Step 4: figures. Writes paper/figures/*.png, stamped DRAFT unless --final.

Plain-language header: two charts. Figure 1 shows how many governments have
finance and full-year energy data each year. Figure 2 shows how many NYPA
projects were completed each year since 1987. The DRAFT stamp comes off only
after you finish the verification checklist.
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from muni import config as C  # noqa: E402

BLUE, ORANGE, INK, MUTED, GRID, SURF = "#2a78d6", "#eb6834", "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb"


def style(ax, title, ylabel):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=12)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=9)


def stamp(fig, final, sample):
    if sample:
        fig.text(0.5, 0.5, "SAMPLE DATA - NOT REAL", ha="center", va="center", fontsize=30,
                 color="#c0392b", alpha=0.18, rotation=20)
    if not final:
        fig.text(0.99, 0.01, "DRAFT - unverified", ha="right", va="bottom", fontsize=9,
                 color="#c0392b")


def main(final: bool) -> None:
    C.FIGS.mkdir(parents=True, exist_ok=True)
    S = json.loads((C.PAPER / "stats.json").read_text())
    sample = S.get("sample_mode", False)
    by = pd.DataFrame(S["by_year"]).T.sort_index()
    by.index = by.index.astype(int)

    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=SURF)
    ax.plot(by.index, by.with_finance, color=BLUE, lw=2, marker="o", ms=5,
            label="With Comptroller finance data")
    ax.plot(by.index, by.full_year_elec, color=ORANGE, lw=2, marker="o", ms=5,
            label="With 12 months of community electricity data")
    for col, colr in (("with_finance", BLUE), ("full_year_elec", ORANGE)):
        ax.annotate(f"{int(by[col].iloc[-1]):,}", (by.index[-1], by[col].iloc[-1]),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
    style(ax, "Figure 1. Governments with data in the MUNI-BENCH panel, by year",
          "Number of local governments")
    ax.set_xticks(by.index)
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc="lower left")
    fig.text(0.01, 0.01, "Sources: NYS Comptroller; NYSERDA Utility Energy Registry. "
             "See paper/stats.json.", fontsize=7, color=MUTED)
    stamp(fig, final, sample)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(C.FIGS / "fig1_panel_coverage.png", dpi=200)
    plt.close(fig)

    nypa = pd.read_csv(C.RAW / "nypa_projects.csv", dtype=str)
    yc = pd.to_numeric(nypa.year_completed, errors="coerce").dropna().astype(int)
    counts = yc.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=SURF)
    colors = [BLUE if C.PANEL_START <= y <= C.PANEL_END else "#9ec5f4" for y in counts.index]
    ax.bar(counts.index, counts.values, color=colors, width=0.8, edgecolor=SURF, linewidth=1)
    ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.text(C.PANEL_START - 0.5, counts.max() * 1.02, "Linked panel 2016 to 2025",
            fontsize=9, color=INK)
    style(ax, f"Figure 2. NYPA public-facility efficiency projects completed per year "
              f"(n = {len(nypa):,})", "Projects completed")
    fig.text(0.01, 0.01, "Source: NYPA Energy Efficiency Completed Projects (data.ny.gov "
             "erjw-j2zx).", fontsize=7, color=MUTED)
    stamp(fig, final, sample)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(C.FIGS / "fig2_nypa_projects_by_year.png", dpi=200)
    plt.close(fig)
    print("Step 4 done.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true")
    main(ap.parse_args().final)
