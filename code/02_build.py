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
    u["accounts"] = pd.to_numeric(u.get("number_of_accounts"), errors="coerce")
    u["withheld"] = u["value"] == -999
    # Negative consumption (other than the -999 privacy code) is treated as an invalid
    # month: it is counted in *_months_invalid and kept out of the totals.
    u["invalid"] = (u["value"] < 0) & ~u["withheld"]
    u.loc[u["withheld"] | u["invalid"], "value"] = pd.NA
    return u


def community_annual(u: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    u = u.copy()
    u["fips"] = u["full_fips"].str.replace(r"\.0+$", "", regex=True).str.strip()
    u["com_type_n"] = u["com_type"].map(normalize_class)
    communities = (u.groupby(["fips", "com_type_n"])
                   .agg(com_name=("com_name", lambda s: s.mode().iat[0] if len(s.mode()) else ""),
                        name_variants=("com_name", lambda s: ";".join(sorted(set(s.dropna())))),
                        counties=("county_name", lambda s: ";".join(sorted(set(s.dropna())))),
                        first_year=("year", "min"), last_year=("year", "max"),
                        n_rows=("year", "size"))
                   .reset_index())
    monthly = (u.groupby(["fips", "data_class", "year", "month"])
               .agg(value=("value", "sum"), any_withheld=("withheld", "any"),
                    any_invalid=("invalid", "any"), accounts=("accounts", "sum"),
                    any_value=("value", lambda s: s.notna().any()))
               .reset_index())
    # A month counts only if every reporting utility gave a valid value.
    monthly["reported"] = monthly["any_value"] & ~monthly["any_withheld"] & ~monthly["any_invalid"]
    monthly.loc[~monthly["reported"], ["value", "accounts"]] = pd.NA
    ann = (monthly.groupby(["fips", "data_class", "year"])
           .agg(total=("value", "sum"), months_reported=("reported", "sum"),
                months_withheld=("any_withheld", "sum"), months_invalid=("any_invalid", "sum"),
                accounts_avg=("accounts", "mean"))
           .reset_index())
    wide = ann.pivot_table(index=["fips", "year"], columns="data_class",
                           values=["total", "months_reported", "months_withheld",
                                   "months_invalid", "accounts_avg"])
    short = {"electricity": "elec", "natural_gas": "gas"}
    wide.columns = [f"{short[c]}_{m}" for m, c in wide.columns]
    wide = wide.rename(columns={"elec_total": "elec_mwh", "gas_total": "gas_therms"}).reset_index()
    for c in ("elec_accounts_avg", "gas_accounts_avg"):
        if c in wide:
            wide[c] = wide[c].round(0)
    return communities, wide


# ------------------------------------------------------------------- linking
def _fuzzy(query, choices: dict, scorer=fuzz.token_sort_ratio):
    if not choices:
        return None, 0
    hit = process.extractOne(query, choices, scorer=scorer)
    return (hit[2], hit[1]) if hit else (None, 0)


def _nospace(s: str) -> str:
    return (s or "").replace(" ", "")


def _county_ok(ek: str, keys: set) -> bool:
    """County match tolerant of UER truncation ('Jeffers'), joint names
    ('Broome & Delaware') and blanks."""
    if not keys:
        return True
    for k in keys:
        if not k:
            return True
        if k == ek or (len(k) >= 4 and (ek.startswith(k) or k.startswith(ek))):
            return True
    return False


def link_uer(ent: pd.DataFrame, comm: pd.DataFrame) -> pd.DataFrame:
    comm = comm.copy()
    comm["name_keys"] = comm["name_variants"].map(
        lambda s: {name_key(x) for x in s.split(";")} | {_nospace(name_key(x)) for x in s.split(";")})
    comm["county_keys"] = comm["counties"].map(
        lambda s: {county_key(p) for x in s.split(";") for p in x.split("&")} if s else set())
    cols = ["municipal_code", "uer_fips", "uer_com_name", "method", "score", "uer_alt_fips"]
    rows = []
    for e in ent[ent.class_n.isin(["city", "town", "village"])].itertuples():
        if pd.notna(e.last_fy) and int(e.last_fy) < C.PANEL_START:
            rows.append((e.municipal_code, None, None, "not_in_panel_years", 0, None)); continue
        pool = comm[(comm.com_type_n == e.class_n) &
                    comm.county_keys.map(lambda ks: _county_ok(e.county_key, ks))]
        exact = pool[pool.name_keys.map(
            lambda ks: e.name_key in ks or _nospace(e.name_key) in ks)]
        if len(exact):
            # Several codes can carry one place (e.g. a code change between protocols).
            # Use the one with the most data; record the others.
            exact = exact.sort_values(["n_rows", "last_year"], ascending=False)
            r = exact.iloc[0]
            alt = ";".join(exact.fips.iloc[1:]) or None
            rows.append((e.municipal_code, r.fips, r.com_name, "exact", 100, alt)); continue
        idx, score = _fuzzy(e.name_key, dict(zip(pool.index, pool.com_name.map(name_key))))
        if idx is not None and score >= C.FUZZY_REVIEW:
            r = pool.loc[idx]
            method = "fuzzy_auto" if score >= C.FUZZY_ACCEPT else "fuzzy_review"
            rows.append((e.municipal_code, r.fips, r.com_name, method, round(score), None))
        else:
            rows.append((e.municipal_code, None, None, "unmatched", round(score), None))
    return pd.DataFrame(rows, columns=cols)


STATE_WORDS = re.compile(r"\bnys\b|new york state|\bsuny\b|\bcuny\b|state university|"
                         r"city university of new york|office of general services|\bogs\b|"
                         r"dormitory authority|port authority|\bmta\b|thruway|correctional|"
                         r"state of new york|metropolitan transportation")
NYC_WORDS = re.compile(r"city of new york|\bnyc\b|new york city|\bny city\b|\bnycha\b")
OTHER_WORDS = re.compile(r"housing authority|community college|universit|\bcollege\b|"
                         r"institute of technology|cooperative|\bboces\b|"
                         r"transit authority|transportation authority|water authority|"
                         r"water board|public library|\blibrary\b|foundation|"
                         r"grant agreement|multiple sites|nyserda funded|\btrust\b|"
                         r"medical center|hospital|development corp|"
                         r"\binc\b|\bcorp\b|\bltd\b|\bllc\b|\bco\.|association|testing lab")


def _clean_customer(c: str, drop_suffix: bool = True) -> str:
    s = re.sub(r"\(.*?\)", " ", c)            # "(NASSAU)"
    s = re.sub(r"\busfd\b", "ufsd", s, flags=re.I)
    if drop_suffix:
        s = re.sub(r"\s+-\s+.*$", " ", s)      # "LYNCOURT UFSD - SALINA"
    return s


def link_nypa(nypa: pd.DataFrame, ent: pd.DataFrame) -> pd.DataFrame:
    ent = ent.assign(nospace=ent.name_key.map(_nospace))
    rows = []
    for p in nypa.itertuples():
        cust = str(p.customer or "")
        low = cust.lower()
        cls = infer_class(_clean_customer(cust, drop_suffix=False))
        ck = county_key(str(p.ny_state_county or ""))
        base = (p.project_code, cust, cls, p.ny_state_county)

        def hit(e, method, score):
            rows.append(base + (e.municipal_code, e.entity_name, method, round(score)))

        if NYC_WORDS.search(low):
            rows.append(base + (None, None, "not_in_scope_nyc", 0)); continue
        if STATE_WORDS.search(low) or (isinstance(p.agency, str) and p.agency.strip()
                                       and cls is None):
            rows.append(base + (None, None, "not_in_scope_state", 0)); continue
        if OTHER_WORDS.search(low):
            rows.append(base + (None, None, "not_in_scope_other", 0)); continue
        key = name_key(_clean_customer(cust))
        incounty = ent[ent.county_key == ck]
        pool = incounty[incounty.class_n == cls] if cls else incounty
        # Tier 1: exact name, same county and class
        exact = pool[(pool.name_key == key) | (pool.nospace == _nospace(key))]
        if len(exact) == 1:
            hit(exact.iloc[0], "exact", 100); continue
        # Tier 2: close spelling, same county and class
        idx, score = _fuzzy(key, dict(zip(pool.index, pool.name_key)))
        if idx is not None and score >= C.FUZZY_REVIEW and (cls or score >= C.FUZZY_ACCEPT):
            method = "fuzzy_auto" if (score >= C.FUZZY_ACCEPT and cls) else "fuzzy_review"
            hit(pool.loc[idx], method, score); continue
        # Tier 3: shortened name ("Allegany CSD" for Allegany-Limestone CSD). Review only.
        idx, score = _fuzzy(key, dict(zip(pool.index, pool.name_key)), fuzz.token_set_ratio)
        if idx is not None and score >= 90 and len(key) >= 4:
            hit(pool.loc[idx], "partial_review", score); continue
        # Tier 4: exact name and class, different county (NYPA county errors). Review only.
        if cls:
            other = ent[(ent.class_n == cls) & ((ent.name_key == key) |
                                                (ent.nospace == _nospace(key)))]
            if len(other) == 1:
                hit(other.iloc[0], "other_county_review", 100); continue
        # Tier 5: same county, class label disagrees (NYPA mislabels). Review only.
        anycls = incounty[(incounty.name_key == key) | (incounty.nospace == _nospace(key))]
        if len(anycls) == 1:
            hit(anycls.iloc[0], "class_mismatch_review", 100); continue
        idx, score = _fuzzy(key, dict(zip(incounty.index, incounty.name_key)), fuzz.token_set_ratio)
        if idx is not None and score >= 95 and len(key) >= 6:
            hit(incounty.loc[idx], "class_mismatch_review", score); continue
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
    # A town and village that share one boundary are reported once by NYSERDA, so both
    # link to the same record. Flag them so users never add the two together.
    shared = ok.uer_fips[ok.uer_fips.duplicated(keep=False)]
    ok["uer_shared_record"] = ok.uer_fips.isin(shared)
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
    who = ent[["municipal_code", "entity_name", "class_n", "county"]]
    rq = pd.concat([
        luer[luer.method == "fuzzy_review"].merge(who, on="municipal_code")
        .assign(source="uer", record_id=lambda d: d.municipal_code,
                left=lambda d: d.entity_name + " (" + d.class_n + ", " + d.county + ")",
                right=lambda d: "NYSERDA record: " + d.uer_com_name),
        lnypa[lnypa.method.str.endswith("_review")].rename(columns={"county": "nypa_county"})
        .merge(who.rename(columns={"entity_name": "e_name"}), on="municipal_code")
        .assign(source="nypa", record_id=lambda d: d.project_code,
                left=lambda d: d.customer + " (NYPA county: " + d.nypa_county.fillna("") + ")",
                right=lambda d: d.e_name + " (" + d.class_n + ", " + d.county + ")"),
    ], ignore_index=True)[["source", "record_id", "method", "left", "right", "score"]]
    rq["decision"] = ""

    zip_ann = zip_companion()

    out = {"entities.csv": ent.drop(columns=["name_key", "county_key"]),
           "link_uer.csv": luer, "link_nypa.csv": lnypa, "review_queue.csv": rq,
           "panel_2016_2025.csv": panel, "community_energy_annual.csv": energy,
           "zip_energy_annual.csv": zip_ann, "uer_communities.csv": comm}
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
