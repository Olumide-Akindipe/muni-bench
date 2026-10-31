"""MUNI-BENCH: New York local government finance, community energy use and NYPA
efficiency projects, linked by government and year (2016 to 2025).

    >>> import muni_bench as mb
    >>> panel = mb.load_panel()                 # latest release
    >>> panel = mb.load_panel(version="0.1.2")  # pin a release for reproducible work

Data are downloaded once from Zenodo (concept DOI 10.5281/zenodo.23314416), checked
against Zenodo's checksum, and cached. Data license: CC BY 4.0. Code license: MIT.
"""
from __future__ import annotations

import os

import pandas as pd

from ._zenodo import (CONCEPT_DOI, KNOWN_ISSUES, MuniBenchError, Release, cache_root, fetch,
                      list_releases, resolve)

__version__ = "0.1.2"

TABLES = {
    "panel": "panel_2016_2025.csv",
    "entities": "entities.csv",
    "link_uer": "link_uer.csv",
    "link_nypa": "link_nypa.csv",
    "community_energy": "community_energy_annual.csv",
    "zip_energy": "zip_energy_annual.csv",
    "uer_communities": "uer_communities.csv",
    "review_queue": "review_queue.csv",
}
_TEXT_IDS = {"municipal_code": str, "uer_fips": str, "fips": str, "project_code": str,
             "zip_code": str, "uer_alt_fips": str}

__all__ = ["load_panel", "load_table", "download", "versions", "citation", "TABLES",
           "MuniBenchError", "Release", "CONCEPT_DOI", "KNOWN_ISSUES", "cache_root", "__version__"]


def download(version: str = "latest", cache_dir: str | os.PathLike | None = None,
             force: bool = False):
    """Download a release (once) and return the local folder holding its tables."""
    return fetch(version, cache_dir=cache_dir, force=force)


def load_table(name: str, version: str = "latest",
               cache_dir: str | os.PathLike | None = None) -> pd.DataFrame:
    """Load one table by short name (see TABLES) or file name."""
    fname = TABLES.get(name, name if name.endswith(".csv") else f"{name}.csv")
    folder = fetch(version, cache_dir=cache_dir)
    path = folder / fname
    if not path.exists():
        have = sorted(p.name for p in folder.glob("*.csv"))
        raise MuniBenchError(f"No table {fname!r} in this release. Tables: {', '.join(have)}")
    head = pd.read_csv(path, nrows=0).columns
    dtype = {c: t for c, t in _TEXT_IDS.items() if c in head}
    df = pd.read_csv(path, dtype=dtype, low_memory=False)
    for c in ("municipal_code",):
        if c in df:  # keep the 12-digit code with its leading zeros
            df[c] = df[c].str.replace(r"\.0$", "", regex=True).str.zfill(12)
    for c in ("uer_fips", "fips"):
        if c in df:
            df[c] = df[c].str.replace(r"\.0+$", "", regex=True)
    return df


def load_panel(version: str = "latest", cache_dir: str | os.PathLike | None = None) -> pd.DataFrame:
    """The linked panel: one row per local government per year, 2016 to 2025."""
    return load_table("panel", version=version, cache_dir=cache_dir)


def versions() -> list[Release]:
    """Every archived release on Zenodo, newest first."""
    return list_releases()


def citation(version: str = "latest") -> str:
    """Suggested citation. Pin a version in published work."""
    r = resolve(version)
    return (f"Akindipe, S. O. ({r.published[:4]}). MUNI-BENCH: Entity-Level Linkage of New York "
            f"Local Government Finance, Community Energy Use, and Public-Facility Efficiency "
            f"Projects (Version {r.version}) [Data set]. Zenodo. https://doi.org/{r.doi}")
