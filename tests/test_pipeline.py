"""End-to-end tests on the synthetic sample. Run: python -m pytest -q tests/"""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
sys.path.insert(0, str(ROOT / "code"))
from muni.names import infer_class, name_key  # noqa: E402


def run(*args):
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True, capture_output=True)


@pytest.fixture(scope="module", autouse=True)
def built():
    run("tests/make_fixture.py")
    run("code/01_fetch.py", "--sample")
    run("code/02_build.py")
    run("code/03_qa.py")


def test_names():
    assert name_key("Village of St. Johnsville") == name_key("SAINT JOHNSVILLE")
    assert name_key("Bethlehem CSD") == name_key("BETHLEHEM CENTRAL SCHOOL DISTRICT")
    assert infer_class("Bethlehem CSD") == "school district"
    assert infer_class("Albany County") == "county"


def test_panel_is_balanced():
    p = pd.read_csv(P / "panel_2016_2025.csv", dtype={"municipal_code": str})
    assert not p.duplicated(["municipal_code", "year"]).any()
    assert len(p) == p.municipal_code.nunique() * 10


def test_multi_utility_months_summed():
    raw = pd.concat([pd.read_csv(ROOT / "data/raw" / f) for f in
                     ("uer_community_2016_2020.csv", "uer_community_2021_on.csv")])
    r = raw[(raw.com_name == "Colonie") & (raw.year == 2019) & (raw.data_class == "electricity")]
    p = pd.read_csv(P / "panel_2016_2025.csv", dtype={"municipal_code": str})
    got = p[(p.entity_name == "COLONIE") & (p.year == 2019)].elec_mwh.iloc[0]
    assert got == pytest.approx(r.value.sum())


def test_withheld_months_excluded():
    p = pd.read_csv(P / "panel_2016_2025.csv", dtype={"municipal_code": str})
    sj = p[(p.entity_name == "SAINT JOHNSVILLE") & (p.year == 2019)].iloc[0]
    assert sj.gas_months_withheld == 2 and sj.gas_months_reported == 10


def test_nypa_scope_and_links():
    l = pd.read_csv(P / "link_nypa.csv")
    assert set(l[l.customer == "City of New York"].method) == {"not_in_scope_nyc"}
    assert set(l[l.customer.str.startswith("NYS")].method) == {"not_in_scope_state"}
    assert set(l[l.customer == "Village of Red Hook"].entity_name) == {"RED HOOK"}
    rh = l[l.customer == "Village of Red Hook"].municipal_code.astype(str).iloc[0]
    assert rh.startswith("140302")   # the village, not the town


def test_review_decision_applied(tmp_path):
    dec = ROOT / "data" / "review_decisions.csv"
    saved = dec.read_text() if dec.exists() else None
    dec.write_text("source,record_id,decision\nnypa,P0002,reject\n")
    try:
        run("code/02_build.py")
        l = pd.read_csv(P / "link_nypa.csv")
        row = l[l.project_code == "P0002"].iloc[0]
        assert not row.accepted and row.method.endswith("author_reject")
    finally:
        if saved is None:
            dec.unlink()
        else:
            dec.write_text(saved)
        run("code/02_build.py")


# ---- Edge cases found in the first real build (2026-10-12) ----
def _panel():
    return pd.read_csv(P / "panel_2016_2025.csv", dtype={"municipal_code": str, "uer_fips": str})


def test_truncated_county_and_spacing():
    l = pd.read_csv(P / "link_uer.csv", dtype=str)
    assert l.set_index("municipal_code").loc["080352100000", "method"] == "exact"


def test_dissolved_entity_not_counted_as_unmatched():
    l = pd.read_csv(P / "link_uer.csv", dtype=str)
    assert l.set_index("municipal_code").loc["040413302710", "method"] == "not_in_panel_years"


def test_shared_record_flagged():
    p = _panel()
    h = p[p.entity_name.str.contains("Harrison")]
    assert h.uer_shared_record.all() and h.uer_fips.nunique() == 1


def test_negative_month_invalid():
    p = _panel()
    b = p[(p.entity_name == "BETHLEHEM") & (p.year == 2017)].iloc[0]
    assert b.elec_months_invalid == 1 and b.elec_months_reported == 11 and b.elec_mwh > 0


def test_two_pieces_same_utility_summed():
    raw = pd.read_csv(ROOT / "data/raw/uer_community_2016_2020.csv")
    r = raw[(raw.com_name == "Red Hook") & (raw.com_type == "Village") & (raw.year == 2019)
            & (raw.data_class == "electricity")]
    assert (r.month == 5).sum() == 2
    p = _panel()
    got = p[(p.municipal_code == "140302000000") & (p.year == 2019)].elec_mwh.iloc[0]
    assert got == pytest.approx(r.value.sum())


def test_accounts_carried():
    p = _panel()
    assert p.elec_accounts_avg.notna().sum() > 0


def test_nypa_new_tiers():
    l = pd.read_csv(P / "link_nypa.csv", dtype=str).drop_duplicates("customer").set_index("customer")
    assert l.loc["NYCHA - NY City Housing Authority", "method"] == "not_in_scope_nyc"
    assert l.loc["SUFFOLK COUNTY COMMUNITY COLLEGE", "method"] == "not_in_scope_other"
    assert l.loc["PERTH, TOWN OF", "method"] == "other_county_review"
    assert l.loc["ALLEGANY CSD", "method"] == "partial_review"
    assert l.loc["PLAINVIEW-OLD BETHPAGE, TOWN OF", "method"] == "class_mismatch_review"
    assert l.loc["RYE NECK USFD", "method"] == "exact"
    rq = pd.read_csv(P / "review_queue.csv")
    assert {"other_county_review", "partial_review", "class_mismatch_review"} <= set(rq.method)
    # review-tier matches never enter the panel until the author accepts them
    acc = pd.read_csv(P / "link_nypa.csv")
    assert not acc[acc.method.str.endswith("_review")].accepted.any()


def test_class_read_before_suffix_removed():
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location("b", ROOT / "code" / "02_build.py")
    b = module_from_spec(spec); spec.loader.exec_module(b)
    assert infer_class(b._clean_customer("NORTHPORT - EAST NORTHPORT SCHOOL", False)) == \
        "school district"


def test_stray_neighbour_name_does_not_capture_link():
    l = pd.read_csv(P / "link_uer.csv", dtype=str).set_index("municipal_code")
    assert l.loc["560302000000", "uer_fips"] == "3612103012"   # Attica keeps its own code
    assert l.loc["560301000000", "uer_fips"] == "3612102418"


def test_school_customer_never_moved_to_village():
    l = pd.read_csv(P / "link_nypa.csv", dtype=str)
    t = l[l.customer == "TARRYTOWN USFD"]
    assert set(t.method) == {"unmatched"}


def test_assign_decision():
    dec = ROOT / "data" / "review_decisions.csv"
    saved = dec.read_text() if dec.exists() else None
    l = pd.read_csv(P / "link_nypa.csv", dtype=str)
    pid = l[l.customer == "TARRYTOWN USFD"].project_code.iloc[0]
    dec.write_text(f"source,record_id,decision,target\nnypa,{pid},assign,550634200100\n")
    try:
        run("code/02_build.py")
        r = pd.read_csv(P / "link_nypa.csv", dtype=str).set_index("project_code").loc[pid]
        assert r.municipal_code == "550634200100" and r.accepted == "True"
        assert r.method.endswith("author_assign") and "Tarrytowns" in r.entity_name
    finally:
        if saved is None:
            dec.unlink()
        else:
            dec.write_text(saved)
        run("code/02_build.py")


def test_other_sources_and_uses_reported_both_ways():
    p = _panel()
    r = p[p.has_finance].iloc[0]
    assert r.revenues_excl_other_sources < r.revenues_total
    assert r.revenues_total / r.revenues_excl_other_sources == pytest.approx(1.7 / 1.2, rel=1e-6)
    assert r.expenditures_excl_other_uses < r.expenditures_total


def test_statement_label_copies_not_double_counted():
    o = pd.read_csv(P / "osc_label_overlap.csv", dtype={"municipal_code": str})
    a = o[(o.municipal_code == "010101000000") & (o.year == 2019)].iloc[0]
    assert a.action == "statement_dropped_as_copy"
    t = o[(o.municipal_code == "010102000000") & (o.year == 2019)].iloc[0]
    assert t.action == "both_kept"
    raw = pd.read_csv(ROOT / "data/raw/osc/osc_sample.csv", dtype=str)
    r = raw[(raw.MUNICIPAL_CODE == "010101000000") & (raw.CALENDAR_YEAR == "2019") &
            (raw.ACCOUNT_CODE_SECTION == "REVENUE")]
    p = _panel()
    got = p[(p.municipal_code == "010101000000") & (p.year == 2019)].revenues_total.iloc[0]
    assert got == pytest.approx(r.AMOUNT.astype(float).sum())


def test_statement_label_is_not_other_sources():
    p = _panel()
    t = p[(p.municipal_code == "010102000000") & (p.year == 2019)].iloc[0]
    # statement-label lines with ordinary account codes count as ordinary revenue
    assert t.revenues_excl_other_sources > 0.5 * t.revenues_total
