#!/usr/bin/env python3
"""Step 2: clean the sources, link them, and build the entity-year panel.

Plain-language header: this script reads the downloaded files, gives every
government one comparable name, matches the Comptroller's governments to the
NYSERDA communities and to the NYPA projects, and writes the final tables to
data/processed/. Every match records how it was made. Matches the computer is
unsure about go to review_queue.csv for you; your decisions go in
data/review_decisions.csv and are applied the next time this runs.
"""
import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).resolve().parent))
from muni import config as C  # noqa: E402
from muni.names import county_key, infer_class, name_key, normalize_class  # noqa: E402

YEARS = list(range(C.PANEL_START, C.PANEL_END + 1))

# ---------------------------------------------------------------- OSC finance
OSC_ALIASES = {  # [VERIFY V1] canonical name: accepted source spellings
    "municipal_code": ["MUNICIPAL_CODE", "MUNI_CODE", "MUNICIPALCODE"],
    "entity_name": ["ENTITY_NAME", "MUNICIPALITY_NAME", "NAME"],
    "class": ["CLASS_DESCRIPTION", "CLASS", "MUNICIPAL_CLASS", "CLASS_OF_GOVERNMENT"],
    "county": ["COUNTY", "COUNTY_NAME"],
    "year": ["CALENDAR_YEAR", "FISCAL_YEAR", "YEAR"],
    "account_code": ["ACCOUNT_CODE"],
    "section": ["ACCOUNT_CODE_SECTION", "FINANCIAL_STATEMENT", "SECTION"],
    "amount": ["AMOUNT", "AMT"],
}


def _read_osc_frames():
    for p in sorted(C.OSC_DROP.glob("*")):
        if p.suffix.lower() == ".csv":
            yield p.name, pd.read_csv(p, dtype=str, low_memory=False)
        elif p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    if n.lower().endswith(".csv"):
                        yield f"{p.name}:{n}", pd.read_csv(io.BytesIO(z.read(n)), dtype=str,
                                                           low_memory=False)


def load_osc() -> pd.DataFrame:
    frames = []
    for label, df in _read_osc_frames():
        cols = {c.strip().upper(): c for c in df.columns}
        ren = {}
        for canon, opts in OSC_ALIASES.items():
            hit = next((cols[o] for o in opts if o in cols), None)
            if hit is None:
                raise SystemExit(f"OSC file {label}: no column for '{canon}'. "
                                 f"Columns found: {list(df.columns)}. Update OSC_ALIASES.")
            ren[hit] = canon
        df = df.rename(columns=ren)[list(OSC_ALIASES)]
        frames.append(df)
    if not frames:
        raise SystemExit("No Comptroller files in data/raw/osc/.")
    osc = pd.concat(frames, ignore_index=True)
    osc["amount"] = pd.to_numeric(osc["amount"].str.replace(",", ""), errors="coerce").fillna(0)
    osc["year"] = pd.to_numeric(osc["year"], errors="coerce").astype("Int64")
    osc["class_n"] = osc["class"].map(normalize_class)
    sec = osc["section"].str.upper().fillna("")
    osc["kind"] = (sec.str.contains("REV").map({True: "revenue"})
                   .fillna(sec.str.contains("EXP").map({True: "expenditure"})))
    osc["function"] = osc["account_code"].fillna("").map(
        lambda s: (re.sub(r"\D", "", s) + "0000")[:4])
    return osc


def build_entities(osc: pd.DataFrame) -> pd.DataFrame:
    last = osc.sort_values("year").groupby("municipal_code").tail(1)
    ent = last[["municipal_code", "entity_name", "class", "class_n", "county"]].copy()
    yrs = osc.groupby("municipal_code")["year"].agg(["min", "max"]).rename(
        columns={"min": "first_fy", "max": "last_fy"})
    ent = ent.merge(yrs, on="municipal_code")
    ent["name_key"] = ent["entity_name"].map(name_key)
    ent["county_key"] = ent["county"].map(county_key)
    return ent.sort_values("municipal_code").reset_index(drop=True)


def build_finance(osc: pd.DataFrame) -> pd.DataFrame:
    d = osc[osc["year"].between(C.PANEL_START, C.PANEL_END)]
    g = d.groupby(["municipal_code", "year"])
    fin = pd.DataFrame({
        "revenues_total": d[d.kind == "revenue"].groupby(["municipal_code", "year"])["amount"].sum(),
        "expenditures_total": d[d.kind == "expenditure"].groupby(
            ["municipal_code", "year"])["amount"].sum(),
    })
    fin = fin.reindex(g.size().index)
    exp = d[d.kind == "expenditure"]
    for label, codes in C.ENERGY_FUNCTIONS.items():
        s = exp[exp["function"].isin(codes)].groupby(["municipal_code", "year"])["amount"].sum()
        fin[f"exp_{label}"] = s
    return fin.reset_index()


# -------------------------------------------------------------- UER community
def load_uer(names) -> pd.DataFrame:
    frames = [pd.read_csv(C.RAW / f"{n}.csv", dtype=str, low_memory=False) for n in names
              if (C.RAW / f"{n}.csv").exists()]
    u = pd.concat(frames, ignore_index=True)
    u = u[u["data_field_display_name"].str.startswith("Total Consumption", na=False)].copy()
    u["unit"] = u["unit"].str.strip().str.lower()
    keep = ((u.data_class == "electricity") & (u.unit == "mwh")) | \
           ((u.data_class == "natural_gas") & (u.unit == "therms"))
    u = u[keep].copy()
    for c in ("year", "month"):
        u[c] = pd.to_numeric(u[c], errors="coerce").astype("Int64")
    u["value"] = pd.to_numeric(u["value"], errors="coerce")
    u["withheld"] = u["value"] == -999
    u.loc[u["withheld"], "value"] = pd.NA
    return u


def community_annual(u: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    u = u.copy()
    u["fips"] = u["full_fips"].str.replace(r"\.0+$", "", regex=True).str.strip()
    u["com_type_n"] = u["com_type"].map(normalize_class)
    communities = (u.groupby(["fips", "com_type_n"])
                   .agg(com_name=("com_name", "first"),
                        counties=("county_name", lambda s: ";".join(sorted(set(s.dropna())))))
                   .reset_index())
    monthly = (u.groupby(["fips", "data_class", "year", "month"])
               .agg(value=("value", "sum"), any_withheld=("withheld", "any"),
                    any_value=("value", lambda s: s.notna().any()))
               .reset_index())
    # A month counts only if every reporting utility gave a value (none withheld).
    monthly["reported"] = monthly["any_value"] & ~monthly["any_withheld"]
    monthly.loc[~monthly["reported"], "value"] = pd.NA
    ann = (monthly.groupby(["fips", "data_class", "year"])
           .agg(total=("value", "sum"), months_reported=("reported", "sum"),
                months_withheld=("any_withheld", "sum"))
           .reset_index())
    wide = ann.pivot_table(index=["fips", "year"], columns="data_class",
                           values=["total", "months_reported", "months_withheld"])
    short = {"electricity": "elec", "natural_gas": "gas"}
    wide.columns = [f"{short[c]}_{m}" for m, c in wide.columns]
    wide = wide.rename(columns={"elec_total": "elec_mwh", "gas_total": "gas_therms"}).reset_index()
    return communities, wide


# ------------------------------------------------------------------- linking
def _fuzzy(query, choices: dict):
    if not choices:
        return None, 0
    hit = process.extractOne(query, choices, scorer=fuzz.token_sort_ratio)
    return (hit[2], hit[1]) if hit else (None, 0)


def link_uer(ent: pd.DataFrame, comm: pd.DataFrame) -> pd.DataFrame:
    comm = comm.copy()
    comm["name_key"] = comm["com_name"].map(name_key)
    comm["county_keys"] = comm["counties"].map(lambda s: {county_key(x) for x in s.split(";")})
    rows = []
    for e in ent[ent.class_n.isin(["city", "town", "village"])].itertuples():
        pool = comm[(comm.com_type_n == e.class_n) &
                    comm.county_keys.map(lambda ks: e.county_key in ks)]
        exact = pool[pool.name_key == e.name_key]
        if len(exact) == 1:
            r = exact.iloc[0]
            rows.append((e.municipal_code, r.fips, r.com_name, "exact", 100))
            continue
        idx, score = _fuzzy(e.name_key, dict(zip(pool.index, pool.name_key)))
        if idx is not None and score >= C.FUZZY_REVIEW:
            r = pool.loc[idx]
            method = "fuzzy_auto" if score >= C.FUZZY_ACCEPT else "fuzzy_review"
            rows.append((e.municipal_code, r.fips, r.com_name, method, round(score)))
        else:
            rows.append((e.municipal_code, None, None, "unmatched", round(score)))
    return pd.DataFrame(rows, columns=["municipal_code", "uer_fips", "uer_com_name",
                                       "method", "score"])


STATE_WORDS = re.compile(r"\bnys\b|new york state|\bsuny\b|\bcuny\b|state university|"
                         r"office of general services|\bogs\b|dormitory authority|"
                         r"port authority|\bmta\b|thruway|correctional|state of new york")
NYC_WORDS = re.compile(r"city of new york|\bnyc\b|new york city")


def link_nypa(nypa: pd.DataFrame, ent: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for p in nypa.itertuples():
        cust = str(p.customer or "")
        low = cust.lower()
        cls = infer_class(cust)
        ck = county_key(str(p.ny_state_county or ""))
        base = (p.project_code, cust, cls, p.ny_state_county)
        if NYC_WORDS.search(low):
            rows.append(base + (None, None, "not_in_scope_nyc", 0)); continue
        if STATE_WORDS.search(low) or (isinstance(p.agency, str) and p.agency.strip()
                                       and cls is None):
            rows.append(base + (None, None, "not_in_scope_state", 0)); continue
        pool = ent[ent.county_key == ck]
        if cls:
            pool = pool[pool.class_n == cls]
        key = name_key(cust)
        exact = pool[pool.name_key == key]
        if len(exact) == 1:
            e = exact.iloc[0]
            rows.append(base + (e.municipal_code, e.entity_name, "exact", 100)); continue
        idx, score = _fuzzy(key, dict(zip(pool.index, pool.name_key)))
        if idx is not None and score >= C.FUZZY_REVIEW and (cls or score >= C.FUZZY_ACCEPT):
            e = pool.loc[idx]
            method = "fuzzy_auto" if (score >= C.FUZZY_ACCEPT and cls) else "fuzzy_review"
            rows.append(base + (e.municipal_code, e.entity_name, method, round(score)))
        else:
            rows.append(base + (None, None, "unmatched", round(score)))
    return pd.DataFrame(rows, columns=["project_code", "customer", "customer_class",
                                       "county", "municipal_code", "entity_name",
                                       "method", "score"])


def apply_review(link: pd.DataFrame, source: str, id_col: str) -> pd.DataFrame:
    """Apply the author's accept/reject decisions from data/review_decisions.csv."""
    link = link.copy()
    link["accepted"] = link["method"].isin(["exact", "fuzzy_auto"])
    f = C.ROOT / "data" / "review_decisions.csv"
    if f.exists():
        d = pd.read_csv(f, dtype=str)
        d = d[d["source"] == source]
        dec = dict(zip(d["record_id"], d["decision"].str.lower()))
        for i, r in link.iterrows():
            v = dec.get(str(r[id_col]))
            if v in ("accept", "reject"):
                link.at[i, "accepted"] = v == "accept"
                link.at[i, "method"] = r["method"] + f"+author_{v}"
    return link


# --------------------------------------------------------------------- panel
def main() -> None:
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    osc = load_osc()
    ent = build_entities(osc)
    fin = build_finance(osc)

    u = load_uer(C.UER_COMMUNITY)
    comm, energy = community_annual(u)
    luer = apply_review(link_uer(ent, comm), "uer", "municipal_code")

    nypa = pd.read_csv(C.RAW / "nypa_projects.csv", dtype=str)
    nypa["year_completed"] = pd.to_numeric(nypa["year_completed"], errors="coerce").astype("Int64")
    for c in ("total_project_cost", "electric_energy_reduction_kwh", "gas_savings_therms",
              "reduction_in_greenhouse_gas_emissions_tons"):
        nypa[c] = pd.to_numeric(nypa[c], errors="coerce")
    lnypa = apply_review(link_nypa(nypa, ent), "nypa", "project_code")

    # Panel spine: every entity x every panel year
    grid = ent[["municipal_code", "entity_name", "class_n", "county"]].merge(
        pd.DataFrame({"year": YEARS}), how="cross")
    panel = grid.merge(fin, on=["municipal_code", "year"], how="left")
    panel["has_finance"] = panel["revenues_total"].notna() | panel["expenditures_total"].notna()

    ok = luer[luer.accepted][["municipal_code", "uer_fips", "method"]].rename(
        columns={"method": "uer_link_method"})
    panel = panel.merge(ok, on="municipal_code", how="left")
    panel = panel.merge(energy.rename(columns={"fips": "uer_fips"}), on=["uer_fips", "year"],
                        how="left")

    pj = nypa.merge(lnypa[lnypa.accepted][["project_code", "municipal_code"]], on="project_code")
    by_year = pj.groupby(["municipal_code", "year_completed"]).agg(
        nypa_projects=("project_code", "count"), nypa_cost=("total_project_cost", "sum"),
        nypa_kwh_savings=("electric_energy_reduction_kwh", "sum"),
        nypa_therm_savings=("gas_savings_therms", "sum"),
        nypa_ghg_tons=("reduction_in_greenhouse_gas_emissions_tons", "sum"),
    ).reset_index().rename(columns={"year_completed": "year"})
    panel = panel.merge(by_year, on=["municipal_code", "year"], how="left")
    for c in ("nypa_projects", "nypa_cost", "nypa_kwh_savings", "nypa_therm_savings",
              "nypa_ghg_tons"):
        panel[c] = panel[c].fillna(0)
    cum = pj.groupby("municipal_code")["year_completed"].apply(list).to_dict()
    panel["nypa_projects_cumulative"] = [
        sum(1 for y in cum.get(m, []) if pd.notna(y) and y <= yr)
        for m, yr in zip(panel.municipal_code, panel.year)]
    panel = panel.rename(columns={"class_n": "class"}).sort_values(["municipal_code", "year"])

    # Review queue for the author
    rq = pd.concat([
        luer[luer.method == "fuzzy_review"].merge(
            ent[["municipal_code", "entity_name", "class_n", "county"]], on="municipal_code")
        .assign(source="uer", record_id=lambda d: d.municipal_code,
                left=lambda d: d.entity_name + " (" + d.class_n + ", " + d.county + ")",
                right=lambda d: d.uer_com_name),
        lnypa[lnypa.method == "fuzzy_review"].assign(
            source="nypa", record_id=lambda d: d.project_code,
            left=lambda d: d.customer + " (" + d.county.fillna("") + ")",
            right=lambda d: d.entity_name),
    ], ignore_index=True)[["source", "record_id", "left", "right", "score"]]
    rq["decision"] = ""

    zip_ann = zip_companion()

    out = {"entities.csv": ent.drop(columns=["name_key", "county_key"]),
           "link_uer.csv": luer, "link_nypa.csv": lnypa, "review_queue.csv": rq,
           "panel_2016_2025.csv": panel, "community_energy_annual.csv": energy,
           "zip_energy_annual.csv": zip_ann}
    for fn, df in out.items():
        df.to_csv(C.PROCESSED / fn, index=False)
        print(f"  wrote {fn}: {len(df):,} rows")
    print("Step 2 done.")


def zip_companion() -> pd.DataFrame:
    try:
        z = load_uer(C.UER_ZIP)
    except ValueError:
        return pd.DataFrame()
    z["zip_code"] = z["zip_code"].str.zfill(5)
    m = (z.groupby(["zip_code", "data_class", "year", "month"])
         .agg(value=("value", "sum"), withheld=("withheld", "any")).reset_index())
    m["reported"] = ~m["withheld"]
    m.loc[m.withheld, "value"] = pd.NA
    return (m.groupby(["zip_code", "data_class", "year"])
            .agg(total=("value", "sum"), months_reported=("reported", "sum"),
                 months_withheld=("withheld", "sum")).reset_index())


if __name__ == "__main__":
    main()
