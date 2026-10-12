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
OSC_ALIASES = {  # canonical name: accepted source spellings
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
    osc["function"] = osc["account_code"].fillna("").map(
        lambda s: (re.sub(r"\D", "", s) + "0000")[:4])
    # Decision V1 (author, 2026-10-12): report totals two ways. "Other sources"
    # (borrowing proceeds, interfund transfers in) and "other uses" (transfers out) are
    # identified by NYS Uniform System of Accounts code ranges: revenue codes 5000-5999,
    # expenditure codes 9900-9999. A section label counts only when it names other
    # sources or uses alone; labels such as "STATEMENT OF REVENUES AND OTHER SOURCES"
    # hold ordinary revenue too and are classed by account code like everything else.
    only_src = sec.str.fullmatch(r"\s*OTHER (FINANCING )?SOURCES?\s*")
    only_use = sec.str.fullmatch(r"\s*OTHER (FINANCING )?USES?\s*")
    rev = sec.str.contains("REV") | only_src
    exp = sec.str.contains("EXP") | only_use
    osc["kind"] = pd.Series(pd.NA, index=osc.index, dtype="object")
    osc.loc[rev, "kind"] = "revenue"
    osc.loc[exp & ~rev, "kind"] = "expenditure"
    osc["other"] = ((osc.kind == "revenue") & (only_src | osc.function.str.startswith("5"))) | \
                   ((osc.kind == "expenditure") & (only_use | osc.function.str.startswith("99")))
    # Label family: the file uses short labels ("REVENUE") and statement labels
    # ("STATEMENT OF REVENUES AND OTHER SOURCES"). Kept so double counting can be checked.
    osc["family"] = sec.str.startswith("STATEMENT").map({True: "statement", False: "short"})
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


def dedupe_families(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Guard against double counting. Where one government-year-kind has rows under
    both label families, compare their (account code, amount) lines. If 90% or more of
    the statement-family lines repeat a short-family line, the statement rows are
    copies and are dropped. Otherwise both are kept. Every case is logged."""
    d = d[d.kind.notna()].copy()
    k = ["municipal_code", "year", "kind"]
    cols = k + ["short_lines", "statement_lines", "short_amount", "statement_amount",
                "statement_share_repeated", "action"]
    fams = d.groupby(k).family.nunique().rename("nfam").reset_index()
    keys = fams[fams.nfam > 1][k]
    if keys.empty:
        return d, pd.DataFrame(columns=cols)
    sub = d.merge(keys, on=k)
    sub["amt2"] = sub.amount.round(2)
    sh = sub[sub.family == "short"][k + ["account_code", "amt2"]].drop_duplicates()
    st = sub[sub.family == "statement"][k + ["account_code", "amt2"]]
    st = st.merge(sh.assign(rep=True), on=k + ["account_code", "amt2"], how="left")
    st["rep"] = st["rep"].fillna(False).astype(bool)
    share = st.groupby(k).rep.mean().rename("statement_share_repeated")
    summ = sub.groupby(k + ["family"]).agg(n=("amount", "size"), amt=("amount", "sum")).unstack("family")
    log = pd.DataFrame({"short_lines": summ[("n", "short")], "statement_lines": summ[("n", "statement")],
                        "short_amount": summ[("amt", "short")].round(2),
                        "statement_amount": summ[("amt", "statement")].round(2)}).join(share)
    log["statement_share_repeated"] = log.statement_share_repeated.round(3)
    log["action"] = log.statement_share_repeated.ge(0.9).map(
        {True: "statement_dropped_as_copy", False: "both_kept"})
    log = log.reset_index()[cols]
    dropkeys = log[log.action == "statement_dropped_as_copy"][k].assign(_drop=True)
    d = d.merge(dropkeys, on=k, how="left")
    d = d[~(d._drop.fillna(False).astype(bool) & (d.family == "statement"))].drop(columns="_drop")
    return d, log


def build_finance(osc: pd.DataFrame) -> pd.DataFrame:
    d = osc[osc["year"].between(C.PANEL_START, C.PANEL_END)]
    d, overlap = dedupe_families(d)
    overlap.to_csv(C.PROCESSED / "osc_label_overlap.csv", index=False)
    g = d.groupby(["municipal_code", "year"])
    k = ["municipal_code", "year"]
    rv, ex = d[d.kind == "revenue"], d[d.kind == "expenditure"]
    fin = pd.DataFrame({
        "revenues_total": rv.groupby(k)["amount"].sum(),
        "revenues_excl_other_sources": rv[~rv.other].groupby(k)["amount"].sum(),
        "expenditures_total": ex.groupby(k)["amount"].sum(),
        "expenditures_excl_other_uses": ex[~ex.other].groupby(k)["amount"].sum(),
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


def _usual_rank(com_name: str, ekey: str) -> int:
    """2: the record's usual spelling is this name. 1: it is this name cut short
    (NYSERDA truncates to 10 characters, e.g. 'Centre Isl'). 0: only a stray spelling
    on some rows matches."""
    k = name_key(com_name)
    if k == ekey or _nospace(k) == _nospace(ekey):
        return 2
    if len(com_name.strip()) >= 7 and len(k) >= 6 and ekey.startswith(k):
        return 1
    return 0


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
            # Several codes can carry one name: a code change between protocols, a
            # truncated spelling ("Great Neck" for Great Neck Estates), or rows labelled
            # with a neighbouring town's name (seen in Wyoming County). Prefer the code
            # whose usual spelling is this government's name; record the others.
            exact = exact.assign(usual=exact.com_name.map(lambda n: _usual_rank(n, e.name_key)))
            exact = exact.sort_values(["usual", "n_rows", "last_year"], ascending=False)
            r = exact.iloc[0]
            alt = ";".join(exact.fips.iloc[1:]) or None
            method = "exact" if r.usual > 0 else "variant_review"
            rows.append((e.municipal_code, r.fips, r.com_name, method, 100, alt)); continue
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
        # Tier 5: same county, class label disagrees (NYPA labels a school district
        # "Town of"). Never moves a school-district customer onto another class.
        if cls == "school district":
            rows.append(base + (None, None, "unmatched", 0)); continue
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


def apply_review(link: pd.DataFrame, source: str, id_col: str, target_col: str,
                 names: dict | None = None) -> pd.DataFrame:
    """Apply the author's decisions from data/review_decisions.csv.

    decision = accept | reject | assign. For assign, the 'target' column holds the
    correct OSC municipal_code (NYPA rows) or NYSERDA fips (UER rows)."""
    link = link.copy()
    link["accepted"] = link["method"].isin(["exact", "fuzzy_auto"])
    f = C.ROOT / "data" / "review_decisions.csv"
    if f.exists():
        d = pd.read_csv(f, dtype=str).fillna("")
        if "target" not in d:
            d["target"] = ""
        d = d[d["source"] == source]
        dec = {r.record_id: (r.decision.strip().lower(), r.target.strip())
               for r in d.itertuples()}
        for i, r in link.iterrows():
            v, tgt = dec.get(str(r[id_col]), ("", ""))
            if v in ("accept", "reject"):
                link.at[i, "accepted"] = v == "accept"
                link.at[i, "method"] = r["method"] + f"+author_{v}"
            elif v == "assign" and tgt:
                link.at[i, target_col] = tgt
                if names is not None:
                    name_col = "entity_name" if source == "nypa" else "uer_com_name"
                    link.at[i, name_col] = names.get(tgt, "")
                link.at[i, "accepted"] = True
                link.at[i, "method"] = r["method"] + "+author_assign"
    return link


# --------------------------------------------------------------------- panel
def main() -> None:
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    osc = load_osc()
    ent = build_entities(osc)
    fin = build_finance(osc)
    (osc.assign(other_i=osc.other.astype(int))
        .groupby(["section", "kind"], dropna=False)
        .agg(rows=("amount", "size"), other_rows=("other_i", "sum"))
        .reset_index().to_csv(C.PROCESSED / "osc_sections.csv", index=False))
    (osc[osc.year.between(C.PANEL_START, C.PANEL_END) & osc.kind.notna()]
        .groupby(["family", "kind", "class_n", "year"], dropna=False)
        .agg(rows=("amount", "size"), amount=("amount", "sum"),
             governments=("municipal_code", "nunique"))
        .reset_index().to_csv(C.PROCESSED / "osc_families_by_year.csv", index=False))

    u = load_uer(C.UER_COMMUNITY)
    comm, energy = community_annual(u)
    luer = apply_review(link_uer(ent, comm), "uer", "municipal_code", "uer_fips",
                        dict(zip(comm.fips, comm.com_name)))

    nypa = pd.read_csv(C.RAW / "nypa_projects.csv", dtype=str)
    nypa["year_completed"] = pd.to_numeric(nypa["year_completed"], errors="coerce").astype("Int64")
    for c in ("total_project_cost", "electric_energy_reduction_kwh", "gas_savings_therms",
              "reduction_in_greenhouse_gas_emissions_tons"):
        nypa[c] = pd.to_numeric(nypa[c], errors="coerce")
    lnypa = apply_review(link_nypa(nypa, ent), "nypa", "project_code", "municipal_code",
                         dict(zip(ent.municipal_code, ent.entity_name)))

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
        luer[luer.method.isin(["fuzzy_review", "variant_review"])].merge(who, on="municipal_code")
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
