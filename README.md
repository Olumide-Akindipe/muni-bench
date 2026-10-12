# MUNI-BENCH

**Status:** v0.1.0, released 2026-10-12, verified by the maintainer | **Maintainer:** Stephen Olumide Akindipe, [ORCID 0000-0002-1846-9662](https://orcid.org/0000-0002-1846-9662) | **License:** code MIT, data CC BY 4.0

**In plain terms:** The State of New York publishes the finances of each local government, how much energy is consumed in each community, and which public buildings and assets received NYPA energy efficiency projects. This information is stored in separate databases that use different names, labels and codes, so it is rarely brought together. This disconnect limits the ability to compare energy investments and policy across local governments. MUNI-BENCH joins this information into a unified table, one row per government per year from 2016 to 2025, and records exactly how each link was made. This allows planners, municipal officers, decision-makers and researchers to compare governments without rebuilding the links themselves.

New here? Read [docs/START_HERE.md](docs/START_HERE.md) first. Terms are explained in [docs/GLOSSARY.md](docs/GLOSSARY.md).

MUNI-BENCH is an open, versioned entity-level linkage of (1) New York State Office of the State Comptroller (OSC) local government financial data, FY1995 to FY2025; (2) NYSERDA Utility Energy Registry (UER) monthly community energy use for cities, towns and villages, 2016 onward; and (3) the New York Power Authority (NYPA) register of completed public-facility energy efficiency projects, 1987 onward. The linked entity-year panel covers 2016 to 2025. The unit is the OSC reporting entity (municipal code). Links to UER communities and NYPA customers are deterministic on normalized name, class of government and county, with a fuzzy fallback whose uncertain cases are adjudicated by the maintainer and recorded in `data/review_decisions.csv`.

## What is here

```
code/01_fetch.py        downloads NYSERDA and NYPA files; logs provenance
code/02_build.py        cleans, links, builds the panel
code/03_qa.py           quality report and paper/stats.json
code/04_figures.py      figures (--final removes the draft label)
code/muni/              configuration and name-matching helpers
data/raw/               inputs (not committed; PROVENANCE.txt is)
data/raw/osc/           place the Comptroller export here
data/processed/         outputs and qa_report.txt
data/review_decisions.csv   maintainer's accept/reject decisions on uncertain links
docs/                   START_HERE, GLOSSARY, BUILD_SPEC, CODEBOOK, LIMITATIONS,
                        VERIFY_CHECKLIST, VERIFICATION_REPORT, DECISIONS,
                        NEXT_STEPS, PUBLISH_GUIDE, TALK_TRACK
tests/                  synthetic fixture and end-to-end tests
```

## Run it

Python 3.10 or newer.

```
pip install -r requirements.txt
# 1. Save the Comptroller export in data/raw/osc/ (see docs/START_HERE.md)
python code/01_fetch.py
python code/02_build.py
python code/03_qa.py
python code/04_figures.py --final
```

Or run it on GitHub: upload the Comptroller file to a release named `osc-input`, then Actions > build-muni-bench > Run workflow. To test the code without any downloads: `python tests/make_fixture.py && python code/01_fetch.py --sample && python code/02_build.py && python code/03_qa.py`, or `python -m pytest -q tests/`.

## Sources

| Source | Dataset | Vintage | Terms | Accessed |
|---|---|---|---|---|
| NYS Office of the State Comptroller, [Financial Data for Local Governments](https://wwe1.osc.state.ny.us/localgov/findata/financial-data-for-local-governments.cfm) | Revenue, expenditure and balance sheet data, all classes, all years | FY1995 to FY2025 | Public record | 2026-10-12 |
| NYSERDA, [UER Monthly Community Energy Use: 2016 to 2021](https://data.ny.gov/d/m3xm-q3dw) | m3xm-q3dw | updated 2026-10-06 | data.ny.gov terms of use | 2026-10-12 |
| NYSERDA, [UER Monthly Community Energy Use: Beginning 2021](https://data.ny.gov/d/4txm-py4p) | 4txm-py4p | updated 2026-10-06 | data.ny.gov terms of use | 2026-10-12 |
| NYSERDA, [UER Monthly ZIP Code Energy Use](https://data.ny.gov/d/tzb9-c2c6) (companion only) | tzb9-c2c6, g2x3-izm4 | updated 2026-10-06 | data.ny.gov terms of use | 2026-10-12 |
| NYPA, [Energy Efficiency Completed Projects: Beginning 1987](https://data.ny.gov/d/erjw-j2zx) | erjw-j2zx, 2,942 projects | updated 2026-07-27 | data.ny.gov terms of use | 2026-10-12 |

Exact files, sizes and SHA-256 fingerprints are in `data/raw/PROVENANCE.txt` after each run.

## Headline numbers

From `paper/stats.json`, build of 2026-10-12, verified by the maintainer.

- **Governments:** 3,264 local governments that report to the State Comptroller (57 counties, 61 cities, 933 towns, 561 villages, 717 school districts, 935 fire districts), giving 32,640 government-years for 2016 to 2025.
- **Energy:** of the 1,536 cities, towns and villages active in 2016 to 2025, 1,504 (97.9%) are linked to a NYSERDA community energy record. 1,485 of these 1,504 have at least one usable annual value (the rest have every month withheld for privacy or invalid). The 32 not linked have no NYSERDA record, mostly villages with their own electric utility or towns that share a boundary with a village.
- **NYPA projects:** of 2,942 completed projects (1987 to 2026), 701 were for local governments that file with the Comptroller. All 701 are linked, to 391 governments; 248 of them were completed in 2016 to 2025. The rest were for New York City (1,490), state bodies (699) and other bodies such as community colleges and authorities (52).
- **Finance:** `revenues_total` and `expenditures_total` are gross sums of the Comptroller file. `revenues_openbook` and `expenditures_openbook` match Open Book New York: in the maintainer's checks they reconcile all 24 sampled totals (12 government-years) to the dollar. Component columns (proceeds of debt, transfers, fiduciary funds, refunding escrow) let users move between the two. See `docs/VERIFICATION_REPORT.md`.

## Limitations

Read [docs/LIMITATIONS.md](docs/LIMITATIONS.md) before using or citing anything here. In short: community energy use is everything consumed inside a city, town or village, not the government's own facilities; fiscal and calendar years differ; NYPA savings are engineering estimates.

## Citation

See `CITATION.cff`. The DOI is issued by Zenodo when the v0.1.0 GitHub release is published and is added here on the same day.

## Related

Companion to the [Verification Gap Ledger](https://doi.org/10.5281/zenodo.23302897) by the same maintainer.
