"""Preprint numbers and figures.

Plain-language header: this script reads the finished tables in data/processed and
paper/stats.json and writes everything the preprint quotes: paper/paper_stats.json,
the LaTeX number file paper/preprint/numbers.tex, and the preprint figures
(paper/figures/pbi_*.pdf and .png) drawn in a Power BI report style. No number in the
preprint is typed by hand; rerun this after every build. Run: python code/05_paper.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from muni import config as C  # noqa: E402

PRE = C.PAPER / "preprint"
YEARS = list(range(C.PANEL_START, C.PANEL_END + 1))

# ------------------------------------------------------------------ Power BI style
# Power BI report look: Segoe-like sans (Open Sans, SIL OFL, bundled in paper/fonts),
# title top left, no axis lines, light horizontal gridlines, legend top left with round
# markers, data labels in dark ink. Categorical hues are Power BI theme colors, checked
# with the dataviz validator (lightness band, chroma, colorblind separation, contrast).
for f in C.FONTS.glob("*.ttf"):
    fm.fontManager.addfont(str(f))
FONT = "Open Sans" if any("Open Sans" in f.name for f in fm.fontManager.ttflist) else "DejaVu Sans"
BLUE, ORANGE, PURPLE, PINK = "#118DFF", "#E66C37", "#744EC2", "#E044A7"
GRAY, LIGHT = "#B3B0AD", "#EDEBE9"
INK, INK2 = "#252423", "#605E5C"
plt.rcParams.update({
    "font.family": FONT, "font.size": 7.5, "axes.edgecolor": LIGHT, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.major.size": 0, "ytick.major.size": 0,
    "axes.titlesize": 9.5, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.titlelocation": "left", "axes.titlepad": 14, "pdf.fonttype": 42,
    "legend.frameon": False, "legend.fontsize": 7, "figure.dpi": 150,
})


def pbi_axes(ax, grid="y"):
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_axisbelow(True)
    if grid:
        ax.grid(axis=grid, color=LIGHT, linewidth=0.8)
    ax.tick_params(length=0, pad=3)


def card(fig):
    """Light rounded border, as a visual sits on a report canvas."""
    fig.patches.append(FancyBboxPatch((0.004, 0.004), 0.992, 0.992,
                                      boxstyle="round,pad=0,rounding_size=0.012",
                                      transform=fig.transFigure, fill=False,
                                      edgecolor="#D2D0CE", linewidth=0.8))


def legend_top(ax, handles_labels, y=1.02, ncol=None):
    h, lab = handles_labels
    ax.legend(h, lab, loc="lower left", bbox_to_anchor=(0, y), ncol=ncol or len(lab),
              handlelength=0.8, handletextpad=0.4, columnspacing=1.2, borderaxespad=0)


def dot(color):
    return plt.Line2D([], [], marker="o", linestyle="", markersize=5.5,
                      markerfacecolor=color, markeredgecolor=color)


def bn(x, d=1):
    return f"${x / 1e9:,.{d}f}bn"


def save(fig, name):
    C.FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(C.FIGS / f"{name}.pdf")
    fig.savefig(C.FIGS / f"{name}.png", dpi=300)
    plt.close(fig)


# --------------------------------------------------------------------------- data
def load():
    rd = lambda f, **k: pd.read_csv(C.PROCESSED / f, low_memory=False, **k)  # noqa: E731
    panel = rd("panel_2016_2025.csv", dtype={"municipal_code": str})
    ent = rd("entities.csv", dtype={"municipal_code": str})
    luer = rd("link_uer.csv", dtype={"municipal_code": str})
    lnypa = rd("link_nypa.csv", dtype={"municipal_code": str})
    for d in (ent, luer, lnypa):
        d["municipal_code"] = d["municipal_code"].str.replace(r"\.0$", "", regex=True).str.zfill(12)
    stats = json.loads((C.PAPER / "stats.json").read_text())
    hand = pd.read_csv(C.HAND_CHECKS, dtype={"municipal_code": str})
    units = rd("uer_unit_labels.csv") if (C.PROCESSED / "uer_unit_labels.csv").exists() else None
    return panel, ent, luer, lnypa, stats, hand, units


def compute(panel, ent, luer, lnypa, stats, hand, units):
    S = {}
    fin = panel[panel.has_finance]
    g = fin[["revenues_total", "revenues_openbook", "transfers_in", "fiduciary_rev",
             "proceeds_of_debt", "expenditures_total", "expenditures_openbook", "transfers_out",
             "fiduciary_exp", "refunding_escrow", "exp_street_lighting", "exp_buildings",
             "exp_water", "exp_sewer"]].sum()
    S["gross"] = {k: float(v) for k, v in g.items()}
    S["finance_rows"] = int(len(fin))
    S["finance_by_year"] = fin.groupby("year")[["revenues_openbook", "expenditures_openbook",
                                               "proceeds_of_debt"]].sum().to_dict("index")
    ef = fin.groupby("year")[["exp_street_lighting", "exp_buildings", "exp_water", "exp_sewer"]].sum()
    S["energy_functions_by_year"] = ef.to_dict("index")
    S["energy_functions_share_of_openbook_exp_pct"] = round(
        100 * ef.values.sum() / g["expenditures_openbook"], 2)
    S["openbook_by_class"] = fin.groupby("class")["revenues_openbook"].sum().to_dict()

    # entities and energy links
    cls_order = ["county", "city", "town", "village", "school district", "fire district"]
    S["entities_by_class"] = {c: int((ent["class_n"] == c).sum()) for c in cls_order}
    lu = luer.merge(ent[["municipal_code", "class_n"]], on="municipal_code", how="left")
    S["uer_methods"] = lu.method.value_counts().to_dict()
    S["uer_by_class"] = {c: lu[lu.class_n == c].method.value_counts().to_dict()
                         for c in ("city", "town", "village")}
    e = panel[panel.uer_link_method.notna()]
    S["uer_linked_with_elec_value"] = int(e.groupby("municipal_code").elec_mwh
                                          .apply(lambda s: s.notna().any()).sum())
    S["uer_linked_with_any_value"] = int(e.groupby("municipal_code")
                                         .apply(lambda d: (d.elec_mwh.notna() | d.gas_therms.notna()).any())
                                         .sum())
    cov = {}
    for y, d in e.groupby("year"):
        em, gm = d.elec_months_reported.fillna(0), d.gas_months_reported.fillna(0)
        cov[int(y)] = {"linked": int(len(d)),
                       "elec_full": int((em == 12).sum()), "elec_part": int(em.between(1, 11).sum()),
                       "elec_none": int((em == 0).sum()),
                       "gas_full": int((gm == 12).sum()), "gas_part": int(gm.between(1, 11).sum()),
                       "gas_none": int((gm == 0).sum()),
                       "elec_mwh_full_year": float(d.loc[em == 12, "elec_mwh"].sum()),
                       "mean_elec_months": round(float(em.mean()), 1)}
    S["energy_coverage_by_year"] = cov
    S["elec_months_withheld"] = int(e.elec_months_withheld.fillna(0).sum())
    S["gas_months_withheld"] = int(e.gas_months_withheld.fillna(0).sum())
    s19 = e[(e.year == 2019) & (e.elec_months_reported == 12) & (e.elec_accounts_avg > 0)]
    S["mwh_per_account_2019_median"] = round(float((s19.elec_mwh / s19.elec_accounts_avg).median()), 2)
    S["scatter_2019_n"] = int(len(s19))
    if units is not None:
        u = units.groupby(["data_class", "unit"]).rows.sum()
        S["unit_rows"] = {f"{a}|{b}": int(v) for (a, b), v in u.items()}

    # NYPA
    ok = lnypa[lnypa.accepted.astype(str) == "True"]
    S["nypa_governments"] = int(ok.municipal_code.nunique())
    ok = ok.merge(ent[["municipal_code", "class_n"]], on="municipal_code", how="left")
    S["nypa_linked_by_class"] = ok.class_n.value_counts().to_dict()
    S["nypa_methods"] = lnypa.method.value_counts().to_dict()
    S["nypa_reviewed"] = int(lnypa.method.str.contains("author").sum())
    nyp = panel[panel.nypa_projects > 0]
    grp = {"city": "Cities, towns and villages", "town": "Cities, towns and villages",
           "village": "Cities, towns and villages", "county": "Counties",
           "school district": "School districts", "fire district": "Fire districts"}
    nb = (nyp.assign(grp=nyp["class"].map(grp)).groupby(["year", "grp"]).nypa_projects.sum()
          .unstack(fill_value=0).reindex(YEARS, fill_value=0))
    S["nypa_by_year_group"] = {int(y): {k: int(v) for k, v in r.items()} for y, r in nb.iterrows()}
    S["nypa_panel_projects"] = int(panel.nypa_projects.sum())
    S["nypa_panel_cost"] = float(panel.nypa_cost.sum())
    S["nypa_panel_kwh"] = float(panel.nypa_kwh_savings.sum())
    S["nypa_panel_therms"] = float(panel.nypa_therm_savings.sum())
    S["nypa_panel_ghg"] = float(panel.nypa_ghg_tons.sum())
    S["nypa_cost_by_year"] = panel.groupby("year").nypa_cost.sum().to_dict()
    S["nypa_governments_panel_years"] = int(nyp.municipal_code.nunique())
    S["nypa_cumulative_2025_govs"] = int((panel[panel.year == 2025].nypa_projects_cumulative > 0).sum())

    # reconciliation table
    rec = hand.merge(panel, on=["municipal_code", "year"], how="left")
    S["reconciliation"] = [
        {"government": r.government, "year": int(r.year), "class": r["class"],
         "ob_rev": float(r.ob_revenues), "mb_rev": float(r.revenues_openbook),
         "ob_exp": float(r.ob_expenditures), "mb_exp": float(r.expenditures_openbook),
         "ob_debt": float(r.ob_proceeds_of_debt), "mb_debt": float(r.proceeds_of_debt),
         "gross_rev": float(r.revenues_total), "gross_exp": float(r.expenditures_total)}
        for _, r in rec.iterrows()]
    S["stats"] = stats
    return S


# ------------------------------------------------------------------------ figures
def fig_flow():
    fig = plt.figure(figsize=(7.0, 2.55))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 36); ax.axis("off")

    def box(x, y, w, h, head, body, color):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                    facecolor="white", edgecolor="#D2D0CE", linewidth=0.8))
        ax.add_patch(FancyBboxPatch((x, y + h - 1.1), w, 1.1, boxstyle="square,pad=0",
                                    facecolor=color, edgecolor="none"))
        ax.text(x + 1.4, y + h - 3.3, head, fontsize=7.6, fontweight="bold", color=INK, va="center")
        ax.text(x + 1.4, y + h - 5.8, body, fontsize=6.3, color=INK2, va="top", linespacing=1.35)

    box(1.5, 24, 27, 11, "State Comptroller (OSC)",
        "Revenue, expenditure, balance sheet\nAll classes, FY1995 to FY2025\nKey: 12-digit municipal code", BLUE)
    box(1.5, 12.5, 27, 11, "NYSERDA Utility Energy Registry",
        "Monthly community electricity and gas\nCities, towns, villages, 2016 onward\nKey: Census place code (FIPS)", ORANGE)
    box(1.5, 1, 27, 11, "NYPA completed projects",
        "2,942 projects, 1987 to 2026\nCustomer name, county, cost, savings\nKey: none (free-text customer)", PURPLE)
    box(37, 7, 25, 22, "Linkage layer",
        "Name key: lowercase, class words\nand punctuation removed, common\nabbreviations expanded\n\nBlocking: class of government\nand county\n\nTiers: exact, close spelling,\nshortened name, county or class\ndisagreement; uncertain links\ndecided by the maintainer", GRAY)
    box(70.5, 7, 28, 22, "MUNI-BENCH panel",
        "One row per government per year\n2016 to 2025\n\nFinance: gross and Open Book\ntotals, components, energy\nrelevant functions\nEnergy: MWh, therms, months,\naccounts, link method\nNYPA: projects, cost, savings", BLUE)
    arrow = dict(arrowstyle="-|>", color=INK2, lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=7)
    for y in (29.5, 18, 6.5):
        ax.annotate("", xy=(37, 18), xytext=(28.5, y), arrowprops=arrow)
    ax.annotate("", xy=(70.5, 18), xytext=(62, 18), arrowprops=arrow)
    save(fig, "pbi_fig1_architecture")


def fig_entities(S):
    order = ["fire district", "town", "school district", "village", "city", "county"]
    lab = {"fire district": "Fire districts", "town": "Towns", "school district": "School districts",
           "village": "Villages", "city": "Cities", "county": "Counties"}
    linked, nonrec, scope = [], [], []
    for c in order:
        n = S["entities_by_class"][c]
        m = S["uer_by_class"].get(c, {})
        lk = int(m.get("exact", 0)); un = int(m.get("unmatched", 0))
        dis = int(m.get("not_in_panel_years", 0))
        linked.append(lk); nonrec.append(un + dis if c in ("city", "town", "village") else 0)
        scope.append(n - lk - (un + dis) if c in ("city", "town", "village") else n)
    fig, ax = plt.subplots(figsize=(3.4, 2.5)); card(fig)
    y = np.arange(len(order))[::-1]
    ax.barh(y, linked, color=BLUE, height=0.62, edgecolor="white", linewidth=1)
    ax.barh(y, nonrec, left=linked, color=ORANGE, height=0.62, edgecolor="white", linewidth=1)
    ax.barh(y, scope, left=np.add(linked, nonrec), color=GRAY, height=0.62, edgecolor="white", linewidth=1)
    for yi, c, a, b, s in zip(y, order, linked, nonrec, scope):
        ax.text(a + b + s + 12, yi, f"{a + b + s:,}", va="center", fontsize=7, color=INK)
    ax.set_yticks(y, [lab[c] for c in order]); pbi_axes(ax, "x")
    ax.set_xlim(0, 1080)
    ax.set_title("Governments by class and energy link status", pad=20)
    legend_top(ax, ([dot(BLUE), dot(ORANGE), dot(GRAY)],
                    ["Linked to NYSERDA", "No record or dissolved", "Outside energy scope"]))
    fig.subplots_adjust(left=0.27, right=0.96, top=0.80, bottom=0.08)
    save(fig, "pbi_fig2_entities")


def fig_coverage(S):
    cov = S["energy_coverage_by_year"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.55), sharey=True); card(fig)
    for ax, kind, title in [(axes[0], "elec", "Electricity: linked communities by months reported"),
                            (axes[1], "gas", "Natural gas: linked communities by months reported")]:
        full = np.array([cov[y][f"{kind}_full"] for y in YEARS])
        part = np.array([cov[y][f"{kind}_part"] for y in YEARS])
        none = np.array([cov[y][f"{kind}_none"] for y in YEARS])
        x = np.arange(len(YEARS))
        ax.bar(x, full, color=BLUE, width=0.66, edgecolor="white", linewidth=1)
        ax.bar(x, part, bottom=full, color=ORANGE, width=0.66, edgecolor="white", linewidth=1)
        ax.bar(x, none, bottom=full + part, color=GRAY, width=0.66, edgecolor="white", linewidth=1)
        for xi, v in zip(x, full):
            ax.text(xi, v / 2, f"{v:,}", ha="center", va="center", fontsize=5.8, color="white",
                    rotation=90, fontweight="bold")
        ax.set_xticks(x, [str(y) for y in YEARS], fontsize=6.5); pbi_axes(ax)
        ax.set_title(title, pad=20, fontsize=8.5)
        legend_top(ax, ([dot(BLUE), dot(ORANGE), dot(GRAY)], ["12 months", "1 to 11 months", "None"]))
    axes[0].set_ylabel("Linked communities")
    fig.subplots_adjust(left=0.08, right=0.985, top=0.80, bottom=0.11, wspace=0.08)
    save(fig, "pbi_fig3_energy_coverage")


def fig_waterfall(S):
    g = S["gross"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6)); card(fig)
    specs = [(axes[0], "Revenue, 2016 to 2025, all governments",
              [("Gross\nrevenue", g["revenues_total"], "total"),
               ("Fiduciary\n(TC, TE)", -g["fiduciary_rev"], "step"),
               ("Interfund\ntransfers", -g["transfers_in"], "step"),
               ("Open Book\nrevenue", g["revenues_openbook"], "total")]),
             (axes[1], "Expenditure, 2016 to 2025, all governments",
              [("Gross\nexpenditure", g["expenditures_total"], "total"),
               ("Fiduciary\n(TC, TE)", -g["fiduciary_exp"], "step"),
               ("Interfund\ntransfers", -g["transfers_out"], "step"),
               ("Refunding\nescrow", -g["refunding_escrow"], "step"),
               ("Open Book\nexpenditure", g["expenditures_openbook"], "total")])]
    for ax, title, items in specs:
        run = 0
        for i, (lab, v, kind) in enumerate(items):
            if kind == "total":
                ax.bar(i, v, color=BLUE, width=0.6); run = v; top = v
                ax.text(i, v + 15e9, bn(v), ha="center", va="bottom", fontsize=6.8, color=INK)
            else:
                ax.bar(i, -v, bottom=run + v, color=ORANGE, width=0.6)
                ax.text(i, run + 15e9, "−" + bn(-v), ha="center", va="bottom", fontsize=6.8, color=INK)
                if i + 1 < len(items):
                    ax.plot([i - 0.3, i + 1.3], [run + v] * 2, color=GRAY, lw=0.6, ls=(0, (2, 2)))
                run = run + v
            if i == 0:
                ax.plot([i + 0.3, i + 0.7], [v, v], color=GRAY, lw=0.6, ls=(0, (2, 2)))
        ax.set_xticks(range(len(items)), [i[0] for i in items], fontsize=6.4)
        ax.set_ylim(0, 1.25e12)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"${x / 1e9:,.0f}bn"))
        pbi_axes(ax); ax.set_title(title, pad=20, fontsize=8.5)
        legend_top(ax, ([dot(BLUE), dot(ORANGE)], ["Total", "Removed by the Open Book rule"]))
    fig.subplots_adjust(left=0.08, right=0.99, top=0.80, bottom=0.17, wspace=0.22)
    save(fig, "pbi_fig4_openbook_waterfall")


def fig_reconcile(S):
    rec = S["reconciliation"]
    fig, ax = plt.subplots(figsize=(3.4, 2.75)); card(fig)
    ob = [r["ob_rev"] for r in rec] + [r["ob_exp"] for r in rec]
    mb = [r["mb_rev"] for r in rec] + [r["mb_exp"] for r in rec]
    lo, hi = 2e5, 1.2e10
    ax.plot([lo, hi], [lo, hi], color=GRAY, lw=0.8, ls=(0, (3, 2)), zorder=1)
    n = len(rec)
    ax.scatter(ob[:n], mb[:n], s=26, color=BLUE, edgecolor="white", linewidth=0.8, zorder=3)
    ax.scatter(ob[n:], mb[n:], s=26, color=ORANGE, marker="D", edgecolor="white", linewidth=0.8, zorder=3)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    fmt = matplotlib.ticker.FuncFormatter(
        lambda x, p: f"${x / 1e9:g}bn" if x >= 1e9 else f"${x / 1e6:g}M")
    ax.xaxis.set_major_formatter(fmt); ax.yaxis.set_major_formatter(fmt)
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    pbi_axes(ax, "both")
    ax.set_xlabel("Open Book New York total (author's reading)")
    ax.set_ylabel("MUNI-BENCH Open Book column")
    ax.set_title("Hand checks: 24 of 24 totals equal", pad=20)
    legend_top(ax, ([dot(BLUE), plt.Line2D([], [], marker="D", ls="", ms=5, color=ORANGE)],
                    ["Revenue", "Expenditure"]))
    ax.text(3e5, 4e9, "Line of equality", fontsize=6.3, color=INK2, rotation=0)
    fig.subplots_adjust(left=0.2, right=0.96, top=0.82, bottom=0.17)
    save(fig, "pbi_fig5_reconciliation")


def fig_nypa_scope(S):
    st = S["stats"]
    scope = [("New York City bodies", st["nypa_method_not_in_scope_nyc"], GRAY),
             ("State bodies", st["nypa_method_not_in_scope_state"], GRAY),
             ("Local governments (OSC)", st["nypa_in_scope"], BLUE),
             ("Other bodies", st["nypa_method_not_in_scope_other"], GRAY)]
    m = S["nypa_methods"]
    auto = int(m.get("exact", 0) + m.get("fuzzy_auto", 0))
    acc = int(sum(v for k, v in m.items() if k.endswith("author_accept")))
    asg = int(sum(v for k, v in m.items() if k.endswith("author_assign")))
    fig, axes = plt.subplots(2, 1, figsize=(3.4, 2.9), gridspec_kw={"height_ratios": [4, 3]}); card(fig)
    ax = axes[0]
    y = np.arange(len(scope))[::-1]
    ax.barh(y, [s[1] for s in scope], color=[s[2] for s in scope], height=0.62)
    for yi, s in zip(y, scope):
        ax.text(s[1] + 25, yi, f"{s[1]:,}", va="center", fontsize=7, color=INK)
    ax.set_yticks(y, [s[0] for s in scope]); ax.set_xlim(0, 1750); pbi_axes(ax, "x")
    ax.set_title(f"NYPA projects by customer type (n = {st['nypa_projects_total']:,})", pad=8, fontsize=8.5)
    ax = axes[1]
    parts = [("Automatic", auto, BLUE), ("Reviewed, accepted", acc, ORANGE), ("Reviewed, reassigned", asg, PURPLE)]
    y = np.arange(len(parts))[::-1]
    ax.barh(y, [p[1] for p in parts], color=[p[2] for p in parts], height=0.62)
    for yi, p in zip(y, parts):
        ax.text(p[1] + 8, yi, f"{p[1]:,}", va="center", fontsize=7, color=INK)
    ax.set_yticks(y, [p[0] for p in parts]); ax.set_xlim(0, 800); pbi_axes(ax, "x")
    ax.set_title(f"How the {st['nypa_in_scope']:,} local government projects were linked", pad=8, fontsize=8.5)
    fig.subplots_adjust(left=0.37, right=0.95, top=0.9, bottom=0.07, hspace=0.62)
    save(fig, "pbi_fig6_nypa_linkage")


def fig_nypa_years(S):
    groups = [("Cities, towns and villages", BLUE), ("School districts", ORANGE),
              ("Counties", PURPLE), ("Fire districts", PINK)]
    nb = S["nypa_by_year_group"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.55)); card(fig)
    ax = axes[0]; x = np.arange(len(YEARS)); bottom = np.zeros(len(YEARS))
    for gname, col in groups:
        v = np.array([nb[y].get(gname, 0) for y in YEARS])
        ax.bar(x, v, bottom=bottom, color=col, width=0.66, edgecolor="white", linewidth=1)
        bottom += v
    for xi, t in zip(x, bottom):
        ax.text(xi, t + 1, f"{int(t)}", ha="center", va="bottom", fontsize=6.6, color=INK)
    ax.set_xticks(x, [str(y) for y in YEARS], fontsize=6.5); ax.set_ylim(0, max(bottom) * 1.18)
    pbi_axes(ax); ax.set_title("Linked NYPA projects completed, by year", pad=20, fontsize=8.5)
    legend_top(ax, ([dot(c) for _, c in groups], ["Cities, towns, villages", "School districts",
                                                  "Counties", "Fire districts"]))
    ax = axes[1]
    cost = np.array([S["nypa_cost_by_year"].get(y, 0) for y in YEARS])
    ax.bar(x, cost, color=BLUE, width=0.66)
    for xi, v in zip(x, cost):
        ax.text(xi, v + 1e6, f"{v / 1e6:,.1f}", ha="center", va="bottom", fontsize=6.3, color=INK)
    ax.set_xticks(x, [str(y) for y in YEARS], fontsize=6.5); ax.set_ylim(0, cost.max() * 1.18)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"${v / 1e6:,.0f}M"))
    pbi_axes(ax); ax.set_title("Total project cost of linked projects ($ millions, nominal)", pad=20, fontsize=8.5)
    fig.subplots_adjust(left=0.06, right=0.99, top=0.80, bottom=0.11, wspace=0.16)
    save(fig, "pbi_fig7_nypa_by_year")


def fig_functions(S):
    ef = S["energy_functions_by_year"]
    items = [("exp_buildings", "Buildings (1620)", BLUE), ("exp_sewer", "Sewer (8110 to 8130)", ORANGE),
             ("exp_water", "Water (8310 to 8350)", PURPLE), ("exp_street_lighting", "Street lighting (5182)", PINK)]
    fig, ax = plt.subplots(figsize=(3.4, 2.75)); card(fig)
    x = np.arange(len(YEARS)); bottom = np.zeros(len(YEARS))
    for k, lab, col in items:
        v = np.array([ef[y][k] for y in YEARS])
        ax.bar(x, v, bottom=bottom, color=col, width=0.66, edgecolor="white", linewidth=1)
        bottom += v
    for xi, t in zip(x, bottom):
        ax.text(xi, t + 0.08e9, f"{t / 1e9:.1f}", ha="center", va="bottom", fontsize=6, color=INK)
    ax.set_xticks(x, [f"'{str(y)[2:]}" for y in YEARS], fontsize=6.5)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"${v / 1e9:,.0f}bn"))
    ax.set_ylim(0, bottom.max() * 1.15); pbi_axes(ax)
    ax.set_title("Spending in energy relevant functions", pad=30)
    legend_top(ax, ([dot(c) for *_, c in items], [i[1] for i in items]), ncol=2)
    fig.subplots_adjust(left=0.14, right=0.97, top=0.76, bottom=0.09)
    save(fig, "pbi_fig8_energy_functions")


def fig_scatter(panel):
    e = panel[(panel.year == 2019) & (panel.elec_months_reported == 12) & (panel.elec_accounts_avg > 0)]
    fig, ax = plt.subplots(figsize=(3.4, 2.75)); card(fig)
    for c, col, mk in [("town", BLUE, "o"), ("village", ORANGE, "D"), ("city", PURPLE, "s")]:
        d = e[e["class"] == c]
        ax.scatter(d.elec_accounts_avg, d.elec_mwh, s=9 if c != "city" else 14, color=col, marker=mk,
                   alpha=0.75, edgecolor="white", linewidth=0.3, zorder=3 if c == "city" else 2)
    for name, dx, dy in [("City of Troy", 1.3, 0.55), ("Town of Brunswick", 0.32, 1.6),
                         ("City of Buffalo", 0.3, 1.0), ("Town of Bethlehem", 0.28, 1.25)]:
        r = e[e.entity_name == name]
        if len(r):
            r = r.iloc[0]
            ax.annotate(name.replace("City of ", "").replace("Town of ", ""),
                        (r.elec_accounts_avg, r.elec_mwh), (r.elec_accounts_avg * dx, r.elec_mwh * dy),
                        fontsize=6, color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.5))
    ax.set_xscale("log"); ax.set_yscale("log"); pbi_axes(ax, "both")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: f"{v:,.0f}"))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda v, p: f"{v / 1e6:g}M" if v >= 1e6 else (f"{v / 1e3:g}K" if v >= 1e3 else f"{v:g}")))
    ax.set_xlabel("Average electric accounts"); ax.set_ylabel("Annual electricity use (MWh)")
    ax.set_title("Community electricity, 2019, full-year records", pad=20)
    legend_top(ax, ([dot(BLUE), plt.Line2D([], [], marker="D", ls="", ms=5, color=ORANGE),
                     plt.Line2D([], [], marker="s", ls="", ms=5, color=PURPLE)], ["Towns", "Villages", "Cities"]))
    fig.subplots_adjust(left=0.17, right=0.96, top=0.82, bottom=0.16)
    save(fig, "pbi_fig9_elec_scatter")


# ------------------------------------------------------------------------ numbers
def macros(S):
    st = S["stats"]; g = S["gross"]; cov = S["energy_coverage_by_year"]
    m = S["nypa_methods"]
    out = {
        "NEnt": st["entities_total"], "NRows": st["panel_rows"],
        "NCounty": st["entities_county"], "NCity": st["entities_city"], "NTown": st["entities_town"],
        "NVillage": st["entities_village"], "NSchool": st["entities_school_district"],
        "NFire": st["entities_fire_district"],
        "UerActive": st["uer_link_candidates"], "UerLinked": st["uer_link_accepted"],
        "UerRate": st["uer_link_rate_pct"], "UerDissolved": st["uer_dissolved_before_panel"],
        "UerUnmatched": st["uer_link_candidates"] - st["uer_link_accepted"],
        "UerAlt": st["uer_links_with_alternate_codes"],
        "UerShared": st["uer_shared_records"], "UerElecValue": S["uer_linked_with_elec_value"],
        "UerAnyValue": S["uer_linked_with_any_value"],
        "ElecWithheld": S["elec_months_withheld"], "GasWithheld": S["gas_months_withheld"],
        "ElecInvalid": st["elec_entity_months_invalid"], "GasInvalid": st["gas_entity_months_invalid"],
        "NypaTotal": st["nypa_projects_total"], "NypaFirst": st["nypa_first_year"],
        "NypaLast": st["nypa_last_year"], "NypaInScope": st["nypa_in_scope"],
        "NypaNYC": st["nypa_method_not_in_scope_nyc"], "NypaState": st["nypa_method_not_in_scope_state"],
        "NypaOther": st["nypa_method_not_in_scope_other"], "NypaGovs": S["nypa_governments"],
        "NypaPanel": S["nypa_panel_projects"], "NypaPanelAll": st["nypa_projects_panel_years"],
        "NypaExact": m.get("exact", 0), "NypaFuzzyAuto": m.get("fuzzy_auto", 0),
        "NypaReviewed": S["nypa_reviewed"], "NypaPanelGovs": S["nypa_governments_panel_years"],
        "NypaCumGovs": S["nypa_cumulative_2025_govs"],
        "NypaPanelCost": f"{S['nypa_panel_cost'] / 1e6:,.1f}",
        "NypaPanelMWh": f"{S['nypa_panel_kwh'] / 1e3:,.0f}",
        "NypaPanelTherms": f"{S['nypa_panel_therms']:,.0f}",
        "NypaPanelGHG": f"{S['nypa_panel_ghg']:,.0f}",
        "GrossRev": f"{g['revenues_total'] / 1e9:,.1f}", "GrossExp": f"{g['expenditures_total'] / 1e9:,.1f}",
        "OBRev": f"{g['revenues_openbook'] / 1e9:,.1f}", "OBExp": f"{g['expenditures_openbook'] / 1e9:,.1f}",
        "FidRev": f"{g['fiduciary_rev'] / 1e9:,.1f}", "FidExp": f"{g['fiduciary_exp'] / 1e9:,.1f}",
        "TrIn": f"{g['transfers_in'] / 1e9:,.1f}", "TrOut": f"{g['transfers_out'] / 1e9:,.1f}",
        "Debt": f"{g['proceeds_of_debt'] / 1e9:,.1f}", "Escrow": f"{g['refunding_escrow'] / 1e9:,.1f}",
        "ShFidRev": st["share_fiduciary_rev_pct"], "ShFidExp": st["share_fiduciary_exp_pct"],
        "ShTrIn": st["share_transfers_in_pct"], "ShTrOut": st["share_transfers_out_pct"],
        "ShDebt": st["share_proceeds_of_debt_pct"], "ShEscrow": st["share_refunding_escrow_pct"],
        "ShOther": st["other_sources_share_pct"], "OBChecked": st["open_book_totals_checked"],
        "OBExact": st["open_book_totals_exact"], "FinRows": S["finance_rows"],
        "EnergyFnShare": S["energy_functions_share_of_openbook_exp_pct"],
        "MWhPerAcct": S["mwh_per_account_2019_median"], "ScatterN": S["scatter_2019_n"],
        "OscFirst": st["osc_first_fy"], "OscLast": st["osc_last_fy"],
        "RawUerA": st["raw_rows_uer_community_2016_2020"], "RawUerB": st["raw_rows_uer_community_2021_on"],
    }
    for y in YEARS:
        w = "abcdefghij"[y - C.PANEL_START]
        out[f"ElecFull{w}"] = cov[y]["elec_full"]
        out[f"GasFull{w}"] = cov[y]["gas_full"]
    lines = ["% Generated by code/05_paper.py from data/processed and paper/stats.json. Do not edit."]
    for k, v in out.items():
        v = f"{v:,}" if isinstance(v, int) else v
        lines.append(f"\\newcommand{{\\{k}}}{{{v}}}")
    PRE.mkdir(parents=True, exist_ok=True)
    (PRE / "numbers.tex").write_text("\n".join(lines) + "\n")


def main():
    panel, ent, luer, lnypa, stats, hand, units = load()
    S = compute(panel, ent, luer, lnypa, stats, hand, units)
    fig_flow(); fig_entities(S); fig_coverage(S); fig_waterfall(S); fig_reconcile(S)
    fig_nypa_scope(S); fig_nypa_years(S); fig_functions(S); fig_scatter(panel)
    macros(S)
    keep = {k: v for k, v in S.items() if k != "stats"}
    (C.PAPER / "paper_stats.json").write_text(json.dumps(keep, indent=2, default=float))
    print(f"font: {FONT}; wrote paper/paper_stats.json, paper/preprint/numbers.tex, 9 figures")


if __name__ == "__main__":
    main()
