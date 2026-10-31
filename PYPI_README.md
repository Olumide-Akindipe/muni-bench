# muni-bench-ny

Load **MUNI-BENCH** in Python: an open panel that links New York local government finances (Office of the State Comptroller), community electricity and natural gas use (NYSERDA Utility Energy Registry) and completed NYPA public-facility efficiency projects. It has one row per government per year, 2016 to 2025, for 3,264 counties, cities, towns, villages, school districts and fire districts.

The package is a small loader. It downloads a release from Zenodo the first time you ask for it, checks it against the checksum Zenodo publishes, caches it and returns pandas DataFrames. The data stay on Zenodo under one citable DOI.

## Install

```
pip install muni-bench-ny
```

The package installs as `muni-bench-ny` and is imported as `muni_bench`. The command line tool is `muni-bench`.

## Use

```python
import muni_bench as mb

panel = mb.load_panel(version="0.1.2")   # pin a release for reproducible work
panel = mb.load_panel()                  # or the latest release

links = mb.load_table("link_nypa")       # other tables: entities, link_uer, community_energy,
                                         # zip_energy, uer_communities, review_queue
for r in mb.versions():                  # every archived release
    print(r.version, r.doi)
print(mb.citation("0.1.2"))
```

Command line:

```
muni-bench versions
muni-bench download --release 0.1.2 --dest muni-bench-data
muni-bench cite --release 0.1.2
```

The cache is in `~/.cache/muni-bench` (on Windows, `%LOCALAPPDATA%\muni-bench`). Set the `MUNI_BENCH_CACHE` environment variable to change it.

## Before you use the numbers

- Community energy is everything consumed inside a city, town or village, not the government's own buildings.
- Finance is by fiscal year; energy and NYPA projects are by calendar year.
- NYPA savings are engineering estimates at completion.
- Release 0.1.1 understates 2021 to 2024 community energy, and the loader warns when you load it. Use 0.1.2 or later.

The full list is in [LIMITATIONS](https://github.com/Olumide-Akindipe/muni-bench/blob/main/docs/LIMITATIONS.md), and every column is described in the [CODEBOOK](https://github.com/Olumide-Akindipe/muni-bench/blob/main/docs/CODEBOOK.md). Both files also come with each download.

## Cite

Akindipe, S. O. (2026). *MUNI-BENCH: Entity-Level Linkage of New York Local Government Finance, Community Energy Use, and Public-Facility Efficiency Projects* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.23314416

Cite the version you used; `mb.citation("<version>")` prints it.

## Licenses

The code is MIT. The data and documents are CC BY 4.0; credit MUNI-BENCH and its sources: the NYS Office of the State Comptroller, NYSERDA and NYPA, via data.ny.gov.

The pipeline that builds the data from the original sources is in the [GitHub repository](https://github.com/Olumide-Akindipe/muni-bench).
