"""Find, download, verify and cache MUNI-BENCH releases from Zenodo.

Every MUNI-BENCH release is archived on Zenodo under one concept DOI. This module
asks Zenodo which versions exist, downloads the archive for the version asked for,
checks it against the checksum Zenodo publishes, and unpacks the data tables into a
local cache so later calls need no network.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
import warnings
import zipfile
from dataclasses import dataclass
from pathlib import Path

CONCEPT_RECORD = "23314416"
CONCEPT_DOI = "10.5281/zenodo.23314416"
API = os.environ.get("MUNI_BENCH_ZENODO_API", "https://zenodo.org/api")
USER_AGENT = "muni-bench-python (+https://github.com/Olumide-Akindipe/muni-bench)"

# Files kept from each archive, besides everything under data/processed/.
DOC_FILES = ("CITATION.cff", "LICENSE-DATA.md", "docs/CODEBOOK.md", "docs/LIMITATIONS.md")

# Releases with no data, or with a documented problem the user should see.
NO_DATA = {"0.1.0": "v0.1.0 archived the code only. Use 0.1.1 or later."}
KNOWN_ISSUES = {
    "0.1.1": ("MUNI-BENCH 0.1.1 understates community energy for 2021 to 2024: NYSEG "
              "electricity (2021 to 2023) and natural gas (2021 to 2024) rows with truncated "
              "unit labels were dropped, and the ZIP companion table omits 2016 to 2020. "
              "Fixed in 0.1.2. Finance and NYPA columns are not affected."),
}


class MuniBenchError(RuntimeError):
    """Raised when a version cannot be found, downloaded or verified."""


@dataclass(frozen=True)
class Release:
    version: str
    record_id: str
    doi: str
    published: str
    file_key: str
    file_url: str
    checksum: str  # "md5:<hex>" as published by Zenodo
    size: int


def _norm(v: str) -> str:
    return str(v).strip().lstrip("vV")


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except Exception as e:  # noqa: BLE001
        raise MuniBenchError(f"Could not reach Zenodo ({url}): {e}") from e


def _release(rec: dict) -> Release | None:
    files = [f for f in rec.get("files", []) if str(f.get("key", "")).endswith(".zip")]
    if not files:
        return None
    f = files[0]
    return Release(version=_norm(rec["metadata"].get("version", "")), record_id=str(rec["id"]),
                   doi=rec.get("doi", ""), published=rec["metadata"].get("publication_date", ""),
                   file_key=f["key"], file_url=f["links"]["self"], checksum=f.get("checksum", ""),
                   size=int(f.get("size", 0)))


def list_releases() -> list[Release]:
    """All archived versions, newest first."""
    # Zenodo lists versions from any record of the series, not from the concept id.
    latest = _get_json(f"{API}/records/{CONCEPT_RECORD}/versions/latest")
    url, hits = f"{API}/records/{latest['id']}/versions?size=25&page=1", []
    while url:
        data = _get_json(url)
        hits += data.get("hits", {}).get("hits", [])
        url = data.get("links", {}).get("next")
    out = [r for r in (_release(h) for h in hits) if r]
    return sorted(out, key=lambda r: tuple(int(x) if x.isdigit() else -1
                                           for x in r.version.split(".")), reverse=True)


def resolve(version: str = "latest") -> Release:
    v = _norm(version)
    if v in NO_DATA:
        raise MuniBenchError(NO_DATA[v])
    if v == "latest":
        r = _release(_get_json(f"{API}/records/{CONCEPT_RECORD}/versions/latest"))
        if r is None:
            raise MuniBenchError("The latest Zenodo record has no archive file.")
        return r
    for r in list_releases():
        if r.version == v:
            return r
    known = ", ".join(r.version for r in list_releases())
    raise MuniBenchError(f"MUNI-BENCH version {version!r} not found on Zenodo. Available: {known}")


def cache_root() -> Path:
    if os.environ.get("MUNI_BENCH_CACHE"):
        return Path(os.environ["MUNI_BENCH_CACHE"]).expanduser()
    base = os.environ.get("XDG_CACHE_HOME") or (
        os.environ.get("LOCALAPPDATA") if os.name == "nt" else None) or Path.home() / ".cache"
    return Path(base) / "muni-bench"


def _verify(path: Path, checksum: str) -> None:
    if not checksum or ":" not in checksum:
        return
    algo, expected = checksum.split(":", 1)
    h = hashlib.new(algo)
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() != expected:
        raise MuniBenchError(f"Checksum mismatch for {path.name}: expected {checksum}, "
                             f"got {algo}:{h.hexdigest()}. Delete the cache and try again.")


def _extract(zpath: Path, dest: Path) -> None:
    tmp = Path(tempfile.mkdtemp(prefix=".partial-", dir=dest.parent))
    try:
        with zipfile.ZipFile(zpath) as z:
            for m in z.infolist():
                if m.is_dir():
                    continue
                parts = Path(m.filename).parts
                rel = Path(*parts[1:]) if len(parts) > 1 else Path(parts[0])  # drop top folder
                keep = rel.parts[:2] == ("data", "processed") or rel.as_posix() in DOC_FILES
                if not keep or ".." in rel.parts:
                    continue
                target = tmp / (rel.relative_to("data/processed") if rel.parts[:2] ==
                                ("data", "processed") else rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(m) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
        if not any(tmp.glob("*.csv")):
            raise MuniBenchError(f"{zpath.name} contains no data/processed tables.")
        if dest.exists():
            shutil.rmtree(dest)
        tmp.rename(dest)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)


def fetch(version: str = "latest", cache_dir: str | os.PathLike | None = None,
          force: bool = False) -> Path:
    """Download (once) and unpack a release. Returns the folder holding its tables."""
    root = Path(cache_dir).expanduser() if cache_dir else cache_root()
    v = _norm(version)
    if v != "latest" and not force:
        hit = root / v
        if (hit / ".complete").exists():
            _warn(v)
            return hit
    rel = resolve(v)
    dest = root / rel.version
    if (dest / ".complete").exists() and not force:
        _warn(rel.version)
        return dest
    root.mkdir(parents=True, exist_ok=True)
    zpath = root / f".{rel.version}.zip"
    req = urllib.request.Request(rel.file_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=300) as r, open(zpath, "wb") as out:
            shutil.copyfileobj(r, out)
        _verify(zpath, rel.checksum)
        _extract(zpath, dest)
    except MuniBenchError:
        raise
    except Exception as e:  # noqa: BLE001
        raise MuniBenchError(f"Download of MUNI-BENCH {rel.version} failed: {e}") from e
    finally:
        zpath.unlink(missing_ok=True)
    (dest / ".complete").write_text(json.dumps(rel.__dict__, indent=2))
    _warn(rel.version)
    return dest


def _warn(v: str) -> None:
    if v in KNOWN_ISSUES:
        warnings.warn(KNOWN_ISSUES[v], stacklevel=3)
