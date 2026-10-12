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
