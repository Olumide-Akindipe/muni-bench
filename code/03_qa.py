#!/usr/bin/env python3
"""Step 3: quality checks. Writes data/processed/qa_report.txt and paper/stats.json.

Plain-language header: this script counts everything, reports how many
governments were matched and how, flags anything that looks wrong, and picks
rows for you to check by hand against the original websites. Read
qa_report.txt before trusting any number. stats.json holds every number that
appears in the README, figures and any paper, so text and data always agree.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from muni import config as C  # noqa: E402

SEED = 20261211
KNOWN = [("albany", "city"), ("troy", "city"), ("colonie", "town"), ("bethlehem", "town"),
         ("red hook", "town"), ("red hook", "village")]


def rows(path: Path) -> int:
    return sum(1 for _ in open(path, encoding="utf-8")) - 1 if path.exists() else 0


def main() -> None:
    P = C.PROCESSED
    ent = pd.read_csv(P / "entities.csv", dtype={"municipal_code": str})
    luer = pd.read_csv(P / "link_uer.csv", dtype={"municipal_code": str, "uer_fips": str})
    lnypa = pd.read_csv(P / "link_nypa.csv", dtype={"municipal_code": str})
    panel = pd.read_csv(P / "panel_2016_2025.csv", dtype={"municipal_code": str,
                                                            "uer_fips": str})
    rq = pd.read_csv(P / "review_queue.csv")
    nypa = pd.read_csv(C.RAW / "nypa_projects.csv", dtype=str)
    sample_mode = "SAMPLE" in (C.RAW / "PROVENANCE.txt").read_text()

    S, out, flags = {}, [], []
    w = out.append
    w("MUNI-BENCH QA REPORT" + ("  [SAMPLE DATA: SYNTHETIC, NOT REAL]" if sample_mode else ""))
    w("DRAFT: unverified until the author completes docs/VERIFY_CHECKLIST.md\n")

    w("1. RAW ROW COUNTS")
    for p in sorted(C.RAW.glob("*.csv")):
        n = rows(p); S[f"raw_rows_{p.stem}"] = n; w(f"   {p.name:40s} {n:>10,}")
    w(f"   OSC files in data/raw/osc/: {len(list(C.OSC_DROP.glob('*')))}")

    w("\n2. ENTITIES (OSC local governments)")
    S["entities_total"] = len(ent)
    for k, v in ent["class_n"].value_counts().items():
        S[f"entities_{k.replace(' ', '_')}"] = int(v); w(f"   {k:20s} {v:>6,}")
    S["osc_first_fy"], S["osc_last_fy"] = int(ent.first_fy.min()), int(ent.last_fy.max())
    w(f"   fiscal years in file: {S['osc_first_fy']} to {S['osc_last_fy']}")
    if ent.municipal_code.duplicated().any():
        flags.append("Duplicate municipal codes in entities.csv")

    w("\n3. OSC -> UER COMMUNITY LINK (cities, towns, villages)")
    acc = luer[luer.accepted.astype(str) == "True"]
    active = luer[luer.method != "not_in_panel_years"]
    S["uer_link_candidates"] = len(active)
    S["uer_dissolved_before_panel"] = int((luer.method == "not_in_panel_years").sum())
    S["uer_link_accepted"] = len(acc)
    S["uer_link_rate_pct"] = round(100 * len(acc) / max(len(active), 1), 1)
    for k, v in luer.method.value_counts().items():
        w(f"   {k:28s} {v:>6,}")
    w(f"   accepted: {len(acc):,} of {len(active):,} active in 2016-2025 "
      f"({S['uer_link_rate_pct']}%); {S['uer_dissolved_before_panel']} dissolved before 2016")
    if "uer_alt_fips" in luer:
        S["uer_links_with_alternate_codes"] = int(luer.uer_alt_fips.notna().sum())
        w(f"   links where NYSERDA used more than one code: {S['uer_links_with_alternate_codes']}")
    dup = acc[acc.uer_fips.duplicated(keep=False)].merge(ent, on="municipal_code")
    S["uer_shared_records"] = int(dup.uer_fips.nunique())
    if len(dup):
        w(f"   shared records (one NYSERDA record, two governments; flagged "
          f"uer_shared_record): {dup.uer_fips.nunique()}")
        for r in dup.itertuples():
            w(f"     {r.uer_fips}  {r.entity_name}")
        import re as _re
        base = dup.assign(core=dup.entity_name.str.replace(
            r"^(Town|Village|City) of ", "", regex=True).str.lower())
        odd = base.groupby("uer_fips").core.nunique()
        odd = odd[odd > 1]
        if len(odd):
            flags.append(f"{len(odd)} shared NYSERDA records link governments with different "
                         f"names (possible mislabelled rows): {', '.join(odd.index)}")
    unl = luer[luer.method == "unmatched"].merge(ent, on="municipal_code")
    if len(unl):
        w(f"   unmatched, all {len(unl)} (likely causes: own municipal electric utility, "
          f"or a town and village reported once):")
        for r in unl.itertuples():
            w(f"     {r.municipal_code}  {r.entity_name} ({r.class_n}, {r.county}, "
              f"last FY {r.last_fy})")

    w("\n4. NYPA PROJECT -> OSC ENTITY LINK")
    S["nypa_projects_total"] = len(nypa)
    yc = pd.to_numeric(nypa.year_completed, errors="coerce")
    S["nypa_first_year"], S["nypa_last_year"] = int(yc.min()), int(yc.max())
    S["nypa_projects_panel_years"] = int(yc.between(C.PANEL_START, C.PANEL_END).sum())
    for k, v in lnypa.method.value_counts().items():
        S[f"nypa_method_{k}"] = int(v); w(f"   {k:28s} {v:>6,}")
    nacc = lnypa[lnypa.accepted.astype(str) == "True"]
    inscope = lnypa[~lnypa.method.str.startswith("not_in_scope")]
    S["nypa_linked"] = len(nacc)
    S["nypa_in_scope"] = len(inscope)
    S["nypa_link_rate_in_scope_pct"] = round(100 * len(nacc) / max(len(inscope), 1), 1)
    w(f"   projects: {len(nypa):,} (completed {S['nypa_first_year']} to {S['nypa_last_year']})")
    w(f"   in local-government scope: {len(inscope):,}; linked: {len(nacc):,} "
      f"({S['nypa_link_rate_in_scope_pct']}%)")

    w("\n5. REVIEW QUEUE")
    S["review_queue"] = len(rq)
    w(f"   {len(rq):,} uncertain matches await your decision (review_queue.csv)")

    w("\n6. PANEL 2016-2025")
    S["panel_rows"] = len(panel)
    S["panel_entities"] = panel.municipal_code.nunique()
    if panel.duplicated(["municipal_code", "year"]).any():
        flags.append("Duplicate entity-year rows in panel")
    w(f"   rows: {len(panel):,}  entities: {S['panel_entities']:,}  years: "
      f"{C.PANEL_START}-{C.PANEL_END}")
    w("   year  with_finance  with_full_year_electricity  mean_elec_months  nypa_projects")
    S["by_year"] = {}
    for y, g in panel.groupby("year"):
        fin = int(g.has_finance.sum())
        el = int((g.get("elec_months_reported", pd.Series(dtype=float)) == 12).sum())
        nyp = int(g.nypa_projects.sum())
        mm = g.get("elec_months_reported", pd.Series(dtype=float)).dropna()
        mm = round(float(mm.mean()), 1) if len(mm) else None
        S["by_year"][int(y)] = {"with_finance": fin, "full_year_elec": el,
                                "mean_elec_months": mm, "nypa_projects": nyp}
        w(f"   {y}  {fin:>12,}  {el:>26,}  {str(mm):>16}  {nyp:>13,}")

    w("\n7. RANGE CHECKS")
    for c in ["revenues_total", "expenditures_total", "elec_mwh", "gas_therms", "nypa_cost"]:
        if c in panel:
            s = panel[c].dropna()
            neg = int((s < 0).sum())
            w(f"   {c:22s} n={len(s):>7,} min={s.min():>16,.0f} max={s.max():>16,.0f} "
              f"negatives={neg}")
            if neg and c not in ("revenues_total", "expenditures_total"):
                flags.append(f"{neg} negative values in {c}")
    withheld = int(panel.get("elec_months_withheld", pd.Series(dtype=float)).fillna(0).sum())
    S["elec_entity_months_withheld"] = withheld
    w(f"   electricity entity-months withheld for privacy: {withheld:,}")
    for k in ("elec", "gas"):
        c = f"{k}_months_invalid"
        if c in panel:
            n = int(panel[c].fillna(0).sum())
            S[f"{k}_entity_months_invalid"] = n
            w(f"   {k} entity-months with a negative value (excluded): {n:,}")

    w("\n8. SPOT CHECKS (check each against the source website)")
    p = panel.merge(ent[["municipal_code", "entity_name"]], on="municipal_code",
                    suffixes=("", "_e"))
    picks = []
    for nm, cl in KNOWN:
        hit = p[(p.entity_name.str.lower().str.contains(nm)) & (p["class"] == cl) &
                (p.year == 2019)]
        if len(hit):
            picks.append(("known", hit.iloc[0]))
    for c in ["elec_mwh", "expenditures_total", "nypa_cost"]:
        if c in p and p[c].notna().any():
            picks.append((f"max {c}", p.loc[p[c].idxmax()]))
    for _, r in p[p.has_finance].sample(min(5, int(p.has_finance.sum())),
                                         random_state=SEED).iterrows():
        picks.append((f"random seed {SEED}", r))
    S["spot_checks"] = []
    for why, r in picks:
        rec = {"why": why, "municipal_code": r.municipal_code, "entity": r.entity_name,
               "year": int(r.year),
               "revenues_total": None if pd.isna(r.revenues_total) else float(r.revenues_total),
               "elec_mwh": None if pd.isna(r.get("elec_mwh")) else float(r.get("elec_mwh")),
               "nypa_projects": int(r.nypa_projects)}
        S["spot_checks"].append(rec)
        w(f"   [{why}] {r.municipal_code} {r.entity_name} ({r['class']}) {int(r.year)}: revenues={rec['revenues_total']} "
          f"elec_mwh={rec['elec_mwh']} nypa_projects={rec['nypa_projects']}")

    w("\n9. FLAGS")
    S["flags"] = flags
    w("\n".join(f"   ! {f}" for f in flags) if flags else "   none")
    S["sample_mode"] = sample_mode

    (P / "qa_report.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    C.PAPER.mkdir(exist_ok=True)
    (C.PAPER / "stats.json").write_text(json.dumps(S, indent=2, default=str), encoding="utf-8")
    print("\n".join(out))
    print("Step 3 done.")


if __name__ == "__main__":
    main()
