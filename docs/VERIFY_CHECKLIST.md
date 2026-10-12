# Your verification checklist

*Plain-language version: before MUNI-BENCH goes public under your name, you check it. Rows and numbers below come from build 2 (2026-10-12); the linkage fixes made after build 2 do not change any value listed here. Total time: about 2 hours, plus the review queue.*

## Part 0: Rule on uncertain matches (done 2026-10-12)

- [x] Open `docs/REVIEW_SUGGESTIONS.md`. It lists every uncertain match with Claude's suggestion and reason. For each, decide accept, reject, or assign (point it at the right government).
- [x] Reply in chat with your decisions (for example "accept all suggestions except Putnam CSD: reject"). Claude writes `data/review_decisions.csv`. Or edit that file yourself: one row per decision, columns `source,record_id,decision,target`.
- [ ] After the next build, `qa_report.txt` section 5 shows 0.

## Part 1: Make sure the results can be rebuilt (15 to 30 min)

Pick one:
- [ ] **Option A, GitHub.** Run the workflow again (PUBLISH_GUIDE Part B, steps 3 to 5). Section 6 of the new `qa_report.txt` should match the previous run exactly.
- [ ] **Option B, ask Claude.** In a new chat, attach the project and the Comptroller zip and say: "Re-run this pipeline from scratch and give me the headline numbers." Compare with section 6 of `qa_report.txt`.

Then:
- [ ] `qa_report.txt` section 1 shows 2,942 NYPA rows, or the difference is explained (NYPA may have added projects).
- [ ] Every number in the README matches `paper/stats.json`.

## Part 2: Check the sources (15 min)

- [ ] Each link in the README Sources table loads and is free.
- [ ] Each dataset's "last updated" date matches or is newer than the README; note any newer edition.
- [ ] data.ny.gov terms of use (link at the bottom of https://data.ny.gov) allow reuse with attribution. Note the wording in LICENSE if it asks for a specific credit line.

## Part 3: Check rows by hand (45 to 60 min)

File: `data/processed/panel_2016_2025.csv`. Find each row by `municipal_code` and `year`.

How to check finance: open https://www.openbooknewyork.com/, choose Local Government, search the name, open Financial Data, pick the year. Open Book may show revenues with or without "other sources" (such as borrowing); note which total matches.

How to check energy: open the NYSERDA dataset, click **View Data**, filter `com_name`, `year`, and `data_field_display_name` = "Total Consumption (T)" with `data_class` = electricity, then add the monthly `value` column. 2016 to 2020: https://data.ny.gov/d/m3xm-q3dw. 2021 on: https://data.ny.gov/d/4txm-py4p.

How to check NYPA: open https://data.ny.gov/d/erjw-j2zx, click **View Data**, filter `customer`.

**Places you know:**
- [ ] City of Albany (010201000000), 2019: revenues_total = 210,651,694; expenditures_total = 203,716,579. Open Book. ___
- [ ] City of Albany, 2019: elec_mwh = 1,189,663.7 over 12 months, about 41,418 accounts. NYSERDA 2016 to 2020. ___
- [ ] Town of Colonie (010318700000), 2019: elec_mwh = 669,921.1, 12 months, about 29,539 accounts. ___
- [ ] Town of Bethlehem (010307100000), 2019: revenues_total = 67,384,459; elec_mwh = 591,294.7. ___
- [ ] Town of Red Hook (130370300000), 2025: revenues_total = 9,437,553; nypa_projects_cumulative = 1. NYPA, filter customer containing "Red Hook". ___
- [ ] Village of Red Hook (130470304160), 2019: revenues_total = 5,175,993; expenditures_total = 2,845,500. Build 3 shows other sources of only about 65,000, so the 2019 jump is ordinary revenue. If you know why (for example a grant), note it here. ___

**Extremes:**
- [ ] City of Buffalo (140207000000), 2018: elec_mwh = 2,786,511.7, the largest in the panel, about 120,218 accounts. NYSERDA 2016 to 2020. ___
- [ ] County of Nassau (280100000000), 2021: revenues_total = 6,339,278,000; expenditures_total = 5,859,773,000, the largest. Open Book. ___
- [ ] City of Syracuse (310255000000), 2021: nypa_cost = 29,843,184, the largest single-year NYPA cost. NYPA, filter customer containing "Syracuse", year 2021. ___

**Random rows (seed 20261211):**
- [ ] Village of Alexandria Bay (220400900080), 2025: revenues_total = 5,733,492; elec_mwh = 12,787.5. ___
- [ ] Marathon Central School District (110750800100), 2020: revenues_total = 18,783,353. ___
- [ ] County of Wyoming (560100000000), 2022: revenues_total = 182,928,913. ___
- [ ] Williamson Central School District (540791000200), 2023: revenues_total = 33,670,030. ___
- [ ] Meadowmere Fire District (281138606000), 2018: revenues_total = 737,008. ___

**Linkage fixes to confirm (5 min):**
- [ ] In `link_uer.csv`, Town of Attica links to code 3612103012 and Town of Arcade to 3612102418. In NYSERDA's file, code 3612102418 carries the name "Attica" on some rows; this is the neighbouring-name error the pipeline now handles. ___

## Part 4: Your decisions (15 min)

- [x] **V1. What counts as revenue.** The pipeline sums every line in the Comptroller's revenue section. Village of Red Hook 2019 shows revenues of 5.18 million against expenditures of 2.85 million, which suggests borrowing proceeds are included. Option A: keep all revenue lines and say so in the codebook. Option B: exclude "other sources" (borrowing, transfers) so revenues reflect taxes, fees and aid only (recommended for comparisons, a small code change). **Decided 2026-10-12:** Report both: `revenues_total` and `revenues_excl_other_sources` (same for expenditures). Comparisons use the excl columns. Confirm in build 4 that `qa_report.txt` section 2 lists the label families and reports how many government-years had both (decision V1a in DECISIONS.md).
- [x] **V2. Energy-relevant spending.** Counted: street lighting 5182, buildings 1620, water 8310 to 8350, sewer 8110 to 8130. Option A: keep as is (recommended). Option B: drop water and sewer, which carry much non-energy cost. **Decided 2026-10-12:** Option A, keep as is.
- [x] **V3. Towns and villages.** Evidence, 2019 average electric accounts: Town of Red Hook 2,457; Village of Red Hook 1,027; Village of Tivoli 735. Town of Colonie 29,539; Village of Colonie 3,371; Village of Menands 2,283. You know Red Hook: does 2,457 look like the whole town, or the town outside its villages? Option A: treat town values as the area outside villages and say so. Option B: say the relationship is unconfirmed and warn users not to add them (recommended unless you are confident). **Decided 2026-10-12:** Option B, relationship unconfirmed; users warned not to add town and village values.
- [x] **V5. Year alignment.** Keep fiscal-year finance beside calendar-year energy, documented in LIMITATIONS 2 (recommended for v0.1), or delay release to build fiscal-period energy. **Decided 2026-10-12:** Recommended: keep fiscal-year finance beside calendar-year energy, documented.
- [x] **V6. Community colleges.** NYPA projects for county-sponsored community colleges (for example Suffolk, Nassau, Westchester) are out of scope. Option A: keep out (recommended; colleges file separately). Option B: credit them to the sponsoring county. **Decided 2026-10-12:** Option A, keep out.
- [x] **V7. Governments with no NYSERDA record.** 32 active governments, listed in `qa_report.txt` section 3. Most are villages known to run their own electric utility (for example Lake Placid, Tupper Lake, Greenport, Bath, Boonville, Hamilton) or towns that share a boundary with a village (Green Island, East Rochester, Mount Kisco, Scarsdale). Option A: leave without energy values and describe the likely causes in LIMITATIONS without naming a cause for each (recommended). Option B: research each before release. **Decided 2026-10-12:** Option A, leave without energy values; likely causes described.
- [x] **V8. Account allocation between neighbours.** In 2019, City of Troy carries about 7,778 electric accounts while the neighbouring Town of Brunswick carries 19,112, far more than its smaller size suggests. This points to the utility assigning some Troy accounts to Brunswick. MUNI-BENCH reports NYSERDA's values as published. Option A: keep as published, flag both in LIMITATIONS, and tell users to check `elec_accounts_avg` (recommended). Option B: drop energy values for both. **Decided 2026-10-12:** Option A, keep as published and flag.

## Part 5: Before it goes public (15 to 30 min)

- [ ] The README "In plain terms" paragraph and the release description are in your own words. (Claude can do this with you line by line.)
- [ ] Name, ORCID, affiliation and email are correct in `AUTHORS.json` and `CITATION.cff`.
- [ ] You have read `docs/LIMITATIONS.md` and agree with it.
- [ ] Figures regenerated with `python code/04_figures.py --final`; README status line changed from DRAFT; `python tools/publish_gate.py . --allow-draft-in tools` passes.
- [ ] Evidence log row written on release day.

**When every box is ticked, tell Claude in your own words that you have checked the package and approve publishing.**
