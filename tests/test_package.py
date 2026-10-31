"""Tests for the muni_bench package (the PyPI data loader).

Offline tests serve a fake Zenodo API from a local web server. The one test marked
"network" downloads a real release; run it with: python -m pytest -m network tests/test_package.py
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import threading
import warnings
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
try:  # the installed package if there is one (CI tests the built wheel), else src/
    import muni_bench as mb
except ImportError:
    sys.path.insert(0, str(ROOT / "src"))
    import muni_bench as mb  # noqa: E402
from muni_bench import _zenodo, cli  # noqa: E402

PANEL = ("municipal_code,entity_name,class,year,revenues_total,uer_fips\n"
         "010201000000,City of Albany,city,2019,210651694.0,3601000.0\n"
         "010307100000,Town of Bethlehem,town,2019,67384459.0,3600106000\n")


def make_zip(top="Olumide-Akindipe-muni-bench-abc1234"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(f"{top}/data/processed/panel_2016_2025.csv", PANEL)
        z.writestr(f"{top}/data/processed/entities.csv", "municipal_code,entity_name\n10201000000,x\n")
        z.writestr(f"{top}/docs/CODEBOOK.md", "# Codebook\n")
        z.writestr(f"{top}/code/02_build.py", "print('not kept')\n")
        z.writestr(f"{top}/../evil.csv", "should never be written\n")
    return buf.getvalue()


class FakeZenodo:
    def __init__(self):
        self.zips = {"23314738": make_zip(), "23315000": make_zip()}
        self.hits = 0
        self.bad_checksum = False
        handler = self._handler()
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.base = f"http://127.0.0.1:{self.srv.server_port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def record(self, rid, version, date):
        data = self.zips.get(rid)
        files = [] if data is None else [{
            "key": f"Olumide-Akindipe/muni-bench-{version}.zip", "size": len(data),
            "checksum": "md5:" + ("0" * 32 if self.bad_checksum else hashlib.md5(data).hexdigest()),
            "links": {"self": f"{self.base}/files/{rid}"}}]
        return {"id": int(rid), "doi": f"10.5281/zenodo.{rid}",
                "metadata": {"version": version, "publication_date": date}, "files": files}

    def _handler(self):
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                recs = [fake.record("23315000", "0.1.2", "2026-11-02"),
                        fake.record("23314738", "0.1.1", "2026-10-12"),
                        fake.record("23314418", "v0.1.0", "2026-10-12")]
                if self.path.startswith("/files/"):
                    fake.hits += 1
                    body, ctype = fake.zips[self.path.rsplit("/", 1)[1]], "application/zip"
                elif self.path.endswith("/versions/latest"):
                    body, ctype = json.dumps(recs[0]).encode(), "application/json"
                elif "/versions" in self.path:
                    body = json.dumps({"hits": {"hits": recs}}).encode()
                    ctype = "application/json"
                else:
                    self.send_response(404); self.end_headers(); return
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        return H


@pytest.fixture()
def zen(monkeypatch, tmp_path):
    f = FakeZenodo()
    monkeypatch.setattr(_zenodo, "API", f.base)
    monkeypatch.setenv("MUNI_BENCH_CACHE", str(tmp_path / "cache"))
    yield f
    f.srv.shutdown()


def test_versions_newest_first_and_normalized(zen):
    assert [r.version for r in mb.versions()] == ["0.1.2", "0.1.1"]  # 0.1.0 has no archive


def test_load_panel_keeps_codes_as_text(zen):
    p = mb.load_panel("0.1.2")
    assert list(p.municipal_code) == ["010201000000", "010307100000"]
    assert list(p.uer_fips) == ["3601000", "3600106000"]
    assert mb.load_table("entities", "0.1.2").municipal_code.iloc[0] == "010201000000"


def test_cache_is_reused(zen):
    mb.load_panel("0.1.2"); mb.load_panel("0.1.2")
    assert zen.hits == 1


def test_only_data_and_docs_are_extracted(zen, tmp_path):
    d = mb.download("0.1.2")
    names = sorted(p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file())
    assert names == [".complete", "docs/CODEBOOK.md", "entities.csv", "panel_2016_2025.csv"]
    assert not (tmp_path / "evil.csv").exists()


def test_latest_resolves(zen):
    assert mb.download().name == "0.1.2"


def test_checksum_mismatch_rejected(zen):
    zen.bad_checksum = True
    with pytest.raises(mb.MuniBenchError, match="Checksum mismatch"):
        mb.load_panel("0.1.2")


def test_code_only_release_explained(zen):
    with pytest.raises(mb.MuniBenchError, match="code only"):
        mb.load_panel("0.1.0")


def test_unknown_version(zen):
    with pytest.raises(mb.MuniBenchError, match="not found"):
        mb.load_panel("9.9.9")


def test_known_issue_warns(zen):
    with pytest.warns(UserWarning, match="understates community energy"):
        mb.load_panel("0.1.1")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        mb.load_panel("0.1.2")


def test_citation_names_version_doi(zen):
    c = mb.citation("0.1.2")
    assert "(Version 0.1.2)" in c and "https://doi.org/10.5281/zenodo.23315000" in c


def test_cli_download_and_cite(zen, tmp_path, capsys):
    out = tmp_path / "out"
    assert cli.main(["download", "--release", "0.1.2", "--dest", str(out)]) == 0
    assert (out / "panel_2016_2025.csv").exists() and not (out / ".complete").exists()
    assert cli.main(["cite", "--release", "0.1.2"]) == 0
    assert "Zenodo" in capsys.readouterr().out
    assert cli.main(["download", "--release", "0.1.0"]) == 1


@pytest.mark.network
def test_real_zenodo_release(tmp_path, monkeypatch):
    monkeypatch.setenv("MUNI_BENCH_CACHE", str(tmp_path))
    with pytest.warns(UserWarning):
        p = mb.load_panel("0.1.1")
    assert len(p) == 32640 and p.municipal_code.str.len().eq(12).all()
