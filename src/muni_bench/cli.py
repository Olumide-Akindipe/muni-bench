"""Command line: muni-bench versions | download | path | cite."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from . import CONCEPT_DOI, KNOWN_ISSUES, MuniBenchError, __version__, citation, download, versions
from ._zenodo import NO_DATA


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="muni-bench", description=(
        "MUNI-BENCH data: New York local government finance, community energy use and NYPA "
        f"projects, 2016 to 2025. Concept DOI {CONCEPT_DOI}."))
    ap.add_argument("--version", action="version", version=f"muni-bench {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("versions", help="list releases archived on Zenodo")
    d = sub.add_parser("download", help="download a release and copy its tables to a folder")
    d.add_argument("--release", default="latest", help="release, e.g. 0.1.2 (default: latest)")
    d.add_argument("--dest", default="muni-bench-data", help="output folder")
    d.add_argument("--force", action="store_true", help="download again even if cached")
    p = sub.add_parser("path", help="print the cache folder for a release (downloads if needed)")
    p.add_argument("--release", default="latest")
    c = sub.add_parser("cite", help="print the suggested citation")
    c.add_argument("--release", default="latest")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "versions":
            for r in versions():
                note = " code only" if r.version in NO_DATA else (
                    " known issue, see docs" if r.version in KNOWN_ISSUES else "")
                print(f"{r.version:<8} {r.published:<11} https://doi.org/{r.doi}  "
                      f"({r.size / 1e6:.1f} MB){note}")
        elif a.cmd == "download":
            src = download(a.release, force=a.force)
            dest = Path(a.dest)
            shutil.copytree(src, dest, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(".complete"))
            print(f"MUNI-BENCH {src.name} tables copied to {dest.resolve()}")
        elif a.cmd == "path":
            print(download(a.release))
        elif a.cmd == "cite":
            print(citation(a.release))
    except MuniBenchError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
