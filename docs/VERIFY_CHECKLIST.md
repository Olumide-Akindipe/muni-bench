# Your verification checklist

*Plain-language version: before MUNI-BENCH goes public under your name, you check it. Rows and numbers below were confirmed unchanged in build 4 (2026-10-12). Total time: about 1.5 hours.*

## Part 0: Rule on uncertain matches (done 2026-10-12)

- [x] Open `docs/REVIEW_SUGGESTIONS.md`. It lists every uncertain match with Claude's suggestion and reason. For each, decide accept, reject, or assign (point it at the right government).
- [x] Reply in chat with your decisions (for example "accept all suggestions except Putnam CSD: reject"). Claude writes `data/review_decisions.csv`. Or edit that file yourself: one row per decision, columns `source,record_id,decision,target`.
- [x] After the next build, `qa_report.txt` section 5 shows 0. (Builds 3 and 4: 0.)

## Part 1: Make sure the results can be rebuilt (15 to 30 min)

Pick one:
- [x] **Option A, GitHub.** (Done: builds 3 and 4 on 2026-10-12 produced identical panels, every column of all 32,640 rows.) Run the workflow again (PUBLISH_GUIDE Part B, steps 3 to 5). Section 6 of the new `qa_report.txt` should match the previous run exactly.
- [ ] (Not needed; Option A done.) **Option B, ask Claude.** In a new chat, attach the project and the Comptroller zip and say: "Re-run this pipeline from scratch and give me the headline numbers." Compare with section 6 of `qa_report.txt`.

Then:
- [x] `qa_report.txt` section 1 shows 2,942 NYPA rows (build 4).
- [x] Every number in the README matches `paper/stats.json` (build 4, checked by Claude 2026-10-12).

## Part 2: Check the sources (15 min)

- [ ] Each link in the README Sources table loads and is free.
- [ ] Each dataset's "last updated" date matches or is newer than the README; note any newer edition.
- [ ] data.ny.gov terms of use (link at the bottom of https://data.ny.gov) allow reuse with attribution. Note the wording in LICENSE if it asks for a specific credit line.

## Part 3: Check rows by hand (done 2026-10-12)

Full record: `MUNI-BENCH_hand_checks_log` in the Project. Finance figures are also in `data/hand_checks.csv`, which every build reconciles automatically.

How to check finance: Open Book New York (https://www.osc.ny.gov/open-book-new-york), Local Government, the government's Revenues and Expenditures trend report. Use the Trend report (Revenues and Expenditures). Compare Open Book with `revenues_openbook` and `expenditures_openbook`, not with the gross totals.

How to check energy: open the NYSERDA dataset, click **View Data**, filter `com_name` and `com_type` (for example Albany and City), `year`, `data_class` = electricity, and `data_field_display_name` = exactly "Total Consumption (T)", then add the monthly `value` column. An unfiltered export mixes neighbouring places and 14 measures. 2016 to 2020: https://data.ny.gov/d/m3xm-q3dw. 2021 on: https://data.ny.gov/d/4txm-py4p.

How to check NYPA: open https://data.ny.gov/d/erjw-j2zx, click **View Data**, filter `customer`.

**Energy (5 of 5 exact):**
- [x] City of Albany 2019: 1,189,663.7 MWh, about 41,418 accounts. Exact.
- [x] Town of Colonie 2019: 669,921.1 MWh, about 29,539 accounts. Exact.
- [x] Town of Bethlehem 2019: 591,294.7 MWh, 14,540 accounts. Exact.
- [x] City of Buffalo 2018, panel maximum: 2,786,511.7 MWh, about 120,218 accounts. Exact.
- [x] Village of Alexandria Bay 2025 (2021-onward file): 12,787.5 MWh. Exact.

**NYPA (2 of 2 exact):**
- [x] City of Syracuse 2021, panel maximum cost: nypa_cost = 29,843,184 (one project, ES-ESN-0725, LED street lighting). Exact.
- [x] Town of Red Hook: nypa_projects_cumulative (since 1987) = 1 in 2025 (ES-ESN-0686, LED street lighting, 2021). Exact. Red Hook CSD's 2024 solar project (ES-ESN-0871) links to Red Hook Central School District, confirmed in `link_nypa.csv`.

**Finance (12 government-years against Open Book):**
- [x] Gross panel totals equal the Comptroller bulk file for all 12 government-years (24 of 24). Against Open Book, a four-part rule (transfers, TC, TE, refunding escrow) reconciles all 24 totals to the dollar; implemented as `revenues_openbook` and `expenditures_openbook` (decision V1r). Confirm the next build's `qa_report.txt` section 2 reports 24 of 24. Full record: docs/VERIFICATION_REPORT.md.
- [x] Village of Red Hook 2019 surplus explained: a state grant of about 2.68 million to the water and sewer enterprise funds (account-level Open Book report). Not borrowing, not a pipeline error.

**Linkage fixes:**
- [x] Town of Attica links to code 3612103012 and Town of Arcade to 3612102418 (`link_uer.csv`, build 4).

## Part 4: Your decisions (15 min)

- [x] **V1. What counts as revenue.** The pipeline sums every line in the Comptroller's revenue section. Village of Red Hook 2019 shows revenues of 5.18 million against expenditures of 2.85 million, which suggests borrowing proceeds are included. Option A: keep all revenue lines and say so in the codebook. Option B: exclude "other sources" (borrowing, transfers) so revenues reflect taxes, fees and aid only (recommended for comparisons, a small code change). **Decided 2026-10-12:** Report both: `revenues_total` and `revenues_excl_other_sources` (same for expenditures). Comparisons use the excl columns. Confirm in build 4 that `qa_report.txt` section 2 lists the label families and reports how many government-years had both (decision V1a in DECISIONS.md).
- [x] **V2. Energy-relevant spending.** Counted: street lighting 5182, buildings 1620, water 8310 to 8350, sewer 8110 to 8130. Option A: keep as is (recommended). Option B: drop water and sewer, which carry much non-energy cost. **Decided 2026-10-12:** Option A, keep as is.
- [x] **V3. Towns and villages.** Evidence, 2019 average electric accounts: Town of Red Hook 2,457; Village of Red Hook 1,027; Village of Tivoli 735. Town of Colonie 29,539; Village of Colonie 3,371; Village of Menands 2,283. You know Red Hook: does 2,457 look like the whole town, or the town outside its villages? Option A: treat town values as the area outside villages and say so. Option B: say the relationship is unconfirmed and warn users not to add them (recommended unless you are confident). **Decided 2026-10-12:** Option B, relationship unconfirmed; users warned not to add town and village values.
- [x] **V5. Year alignment.** Keep fiscal-year finance beside calendar-year energy, documented in LIMITATIONS 2 (recommended for v0.1), or delay release to build fiscal-period energy. **Decided 2026-10-12:** Recommended: keep fiscal-year finance beside calendar-year energy, documented.
- [x] **V6. Community colleges.** NYPA projects for county-sponsored community colleges (for example Suffolk, Nassau, Westchester) are out of scope. Option A: keep out (recommended; colleges file separately). Option B: credit them to the sponsoring county. **Decided 2026-10-12:** Option A, keep out.
- [x] **V7. Governments with no NYSERDA record.** 32 active governments, listed in `qa_report.txt` section 3. Most are villages known to run their own electric utility (for example Lake Placid, Tupper Lake, Greenport, Bath, Boonville, Hamilton) or towns that share a boundary with a village (Green Island, East Rochester, Mount Kisco, Scarsdale). Option A: leave without energy values and describe the likely causes in LIMITATIONS without naming a cause for each (recommended). Option B: research each before release. **Decided 2026-10-12:** Option A, leave without energy values; likely causes described.
- [x] **V8. Account allocation between neighbours.** In 2019, City of Troy carries about 7,778 electric accounts while the neighbouring Town of Brunswick carries 19,112, far more than its smaller size suggests. This points to the utility assigning some Troy accounts to Brunswick. MUNI-BENCH reports NYSERDA's values as published. Option A: keep as published, flag both in LIMITATIONS, and tell users to check `elec_accounts_avg` (recommended). Option B: drop energy values for both. **Decided 2026-10-12:** Option A, keep as published and flag.

## Part 5: Before it goes public (15 to 30 min)

- [x] The README "In plain terms" paragraph and the release description are in your own words (2026-10-12, with corrections you approved; DECISIONS T1). (Claude can do this with you line by line.)
- [ ] Name, ORCID, affiliation and email are correct in `AUTHORS.json` and `CITATION.cff`.
- [ ] You have read `docs/LIMITATIONS.md` and agree with it.
- [ ] Figures regenerated with `python code/04_figures.py --final`; README status line changed from DRAFT; `python tools/publish_gate.py . --allow-draft-in tools code docs/GLOSSARY.md docs/VERIFY_CHECKLIST.md` passes.
- [ ] Evidence log row written on release day.

**When every box is ticked, tell Claude in your own words that you have checked the package and approve publishing.**
