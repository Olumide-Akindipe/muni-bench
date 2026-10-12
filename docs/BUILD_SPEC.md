# MUNI-BENCH build spec

*Plain-language header: this is the one-page plan the whole build follows. You do not need to edit it. If the project changes shape, this file changes first. A plain reading of each line is in the right-hand notes below the spec.*

```
PROJECT:        MUNI-BENCH. Archetype: open dataset (1), with a data descriptor
                paper planned for a later release.
QUESTION:       For each New York city, town, village, county and school district,
                what did it spend and raise each year, how much electricity and gas
                was used in its community, and which public-facility efficiency
                projects did NYPA complete for it?
SOURCES:        1. NYS Office of the State Comptroller (OSC), Financial Data for Local
                   Governments, revenue/expenditure CSV, all classes, all years
                   (FY1995 to FY2025). Bulk export form:
                   https://wwe1.osc.state.ny.us/localgov/findata/financial-data-for-local-governments.cfm
                   Manual download (form, no direct URL). Public record.
                2. NYSERDA Utility Energy Registry (UER), Monthly Community Energy Use,
                   city/town/village level. 2016 to 2020: data.ny.gov m3xm-q3dw.
                   2021 onward: data.ny.gov 4txm-py4p. Both last updated 2026-10-06.
                3. NYSERDA UER Monthly ZIP Code Energy Use (companion table only).
                   2016 to 2021 protocol: tzb9-c2c6. Beginning 2021: g2x3-izm4.
                   Covers Con Edison and National Grid only, with year gaps.
                4. NYPA Energy Efficiency Completed Projects: Beginning 1987,
                   data.ny.gov erjw-j2zx, 2,942 rows, completed 1987 to 2026,
                   last updated 2026-07-27.
UNIT:           Entity-year. Entity = one OSC local government (municipal code).
                Linked panel years: 2016 to 2025.
MEASURES:       Finance: total revenues; total expenditures; expenditures in
                  energy-relevant functions (street lighting, buildings, water, sewer).
                Energy: annual community electricity use (MWh) and natural gas use
                  (therms), summed across utilities; months reported; months withheld
                  for privacy.
                NYPA: projects completed in the year; total project cost; estimated
                  annual kWh, therm and CO2 savings; cumulative projects since 1987.
                Link quality: how each entity was matched to UER and NYPA records
                  (exact, reviewed fuzzy, or unmatched with reason).
OUTPUTS:        data/processed/entities.csv          one row per OSC entity
                data/processed/link_uer.csv          OSC entity to UER community
                data/processed/link_nypa.csv         NYPA project to OSC entity
                data/processed/review_queue.csv      uncertain matches for the author
                data/processed/panel_2016_2025.csv   the linked entity-year panel
                data/processed/zip_energy_annual.csv companion ZIP table
                data/processed/qa_report.txt, paper/stats.json, paper/figures/*.png
VENUES:         GitHub (Olumide-Akindipe/muni-bench), Zenodo DOI (v0.1.0, Dec 2026).
                Later: data descriptor (e.g. Data in Brief or Scientific Data).
VERIFY POINTS:  V1 OSC file column names and the revenue/expenditure section field.
                V2 Which OSC account codes count as "energy-relevant".
                V3 Whether a UER town total includes the villages inside the town.
                V4 Every fuzzy match in review_queue.csv.
                V5 Fiscal-year versus calendar-year alignment (see LIMITATIONS).
LICENSE:        Code MIT. Derived data and documents CC BY 4.0, attributing OSC,
                NYSERDA, NYPA and data.ny.gov.
DECISIONS:      Community-level UER replaces ZIP-level UER as the panel's energy
                layer (author confirmed 2026-10-11). Counties get finance and NYPA only
                in v0.1; county energy is a v0.5 item.
```

## What each line means for you

- **Unit: entity-year.** Every row of the final table is one local government in one year, for example "Town of Colonie, 2019".
- **Sources.** Four free public sources. Three download automatically. The Comptroller file is one zip you download by hand from a form.
- **Measures.** Three groups of columns: money, energy, and NYPA projects. A fourth group says how confident each link is.
- **Outputs.** Six tables, a quality report, a stats file every number in the text comes from, and two figures.
- **Verify points.** Five decisions only you should make. They are written as plain questions in `VERIFY_CHECKLIST.md`.
