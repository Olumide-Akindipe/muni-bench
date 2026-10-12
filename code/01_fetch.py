#!/usr/bin/env python3
"""Step 1: download every public input and record where it came from.

Plain-language header: this script downloads the NYSERDA energy files and the
NYPA project list from data.ny.gov, checks that the Comptroller file you saved
is in data/raw/osc/, and writes a receipt for each file (size, fingerprint,
link, date) to data/raw/PROVENANCE.txt.

Usage:
  python code/01_fetch.py            # real data (needs internet access to data.ny.gov)
  python code/01_fetch.py --sample   # copy the small made-up test sample instead
"""
import argparse
import datetime
import hashlib
import shutil
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from muni import config as C  # noqa: E402

PAGE = 50_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def log(path: Path, url: str, note: str = "") -> None:
    line = " | ".join([datetime.date.today().isoformat(), path.name,
                       f"{path.stat().st_size} bytes", f"sha256:{sha256(path)}", url, note])
    with open(C.RAW / "PROVENANCE.txt", "a", encoding="utf-8") as f:
        f.write(line.rstrip(" |") + "\n")
    print("  logged", path.name)


def socrata_paged(dataset_id: str, out: Path, where: str | None = None) -> str:
    """Download a data.ny.gov dataset as CSV in pages, ordered by row id."""
    import requests
    base = C.SOCRATA.format(id=dataset_id)
    params = {"$order": ":id", "$limit": PAGE}
    if where:
        params["$where"] = where
    offset, first = 0, True
    with open(out, "w", encoding="utf-8", newline="") as fh:
        while True:
            q = dict(params, **{"$offset": offset})
            for attempt in range(5):
                r = requests.get(base, params=q, timeout=120)
                if r.status_code == 200:
                    break
                time.sleep(2 ** attempt)
            r.raise_for_status()
            lines = r.text.splitlines(keepends=True)
            if len(lines) <= 1:
                break
            fh.writelines(lines if first else lines[1:])
            first = False
            offset += PAGE
            print(f"  {dataset_id}: {offset:,} rows requested")
            if len(lines) - 1 < PAGE:
                break
    return base + "?" + urllib.parse.urlencode(params)


def fetch_real() -> None:
    C.RAW.mkdir(parents=True, exist_ok=True)
    for name, ds in {**C.UER_COMMUNITY, **C.UER_ZIP}.items():
        out = C.RAW / f"{name}.csv"
        url = socrata_paged(ds, out, where=C.UER_TOTAL_FILTER)
        log(out, url, f"total-consumption rows only; landing {C.SOCRATA_LANDING.format(id=ds)}")
    for name, ds in C.NYPA.items():
        out = C.RAW / f"{name}.csv"
        url = socrata_paged(ds, out)
        log(out, url, f"full dataset; landing {C.SOCRATA_LANDING.format(id=ds)}")
    osc_files = sorted(p for p in C.OSC_DROP.glob("*") if p.suffix.lower() in (".zip", ".csv"))
    if not osc_files:
        sys.exit("\nComptroller file missing. Download it from\n  " + C.OSC_FORM_URL +
                 "\nand save it in data/raw/osc/ (see docs/START_HERE.md, 'Your one download').")
    for p in osc_files:
        log(p, C.OSC_FORM_URL, "manual export: Revenue, Expenditure and Balance Sheet Data, "
                               "All Classes of Government for All Years")


def fetch_sample() -> None:
    """Use the made-up fixture. It is fake data for testing the code only."""
    if not (C.SAMPLE / "nypa_projects.csv").exists():
        sys.exit("No sample found. Run: python tests/make_fixture.py")
    C.RAW.mkdir(parents=True, exist_ok=True)
    (C.RAW / "osc").mkdir(exist_ok=True)
    for p in C.SAMPLE.glob("*.csv"):
        dest = C.RAW / "osc" / p.name if p.name.startswith("osc_") else C.RAW / p.name
        shutil.copy(p, dest)
        log(dest, "SAMPLE (synthetic fixture, not real data)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    a = ap.parse_args()
    prov = C.RAW / "PROVENANCE.txt"
    if prov.exists():
        prov.unlink()
    fetch_sample() if a.sample else fetch_real()
    print("Step 1 done.")
