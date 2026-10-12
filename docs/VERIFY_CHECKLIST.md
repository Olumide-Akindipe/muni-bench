# Your verification checklist

*Plain-language version: before MUNI-BENCH goes public under your name, you check it. This version is the frame; after the first real build, Claude fills every [bracket] with real rows, numbers and links. Total time: about 1.5 to 2.5 hours, plus the review queue.*

## Part 0: Rule on uncertain matches (30 to 60 min)

- [ ] Open `data/processed/review_queue.csv`. For each row, "left" is the name being matched and "right" is the proposed match. If they are the same government, write `accept` in the decision column; if not, `reject`.
- [ ] Copy the decided rows (source, record_id, decision) into `data/review_decisions.csv`, then re-run `python code/02_build.py` and `python code/03_qa.py`. The queue count in `qa_report.txt` section 5 should drop to 0.

## Part 1: Make sure the results can be rebuilt (15 to 30 min)

Pick one:
- [ ] **Option A, GitHub.** Run the workflow again (PUBLISH_GUIDE Part B, steps 3 to 5) and compare the new `qa_report.txt` with the old one. Section 6 counts should match exactly.
- [ ] **Option B, ask Claude.** In a new chat, attach the project and the Comptroller zip and say: "Re-run this pipeline from scratch and give me the headline numbers." Compare with: [headline numbers from stats.json].

Then:
- [ ] `qa_report.txt` section 1 shows 2,942 NYPA rows, or the difference is explained (NYPA may have added projects).
- [ ] Every number in the README matches `paper/stats.json`.

## Part 2: Check the sources (15 min)

- [ ] Each link in the README Sources table loads and is free.
- [ ] Each dataset's "last updated" date matches or is newer than the README; note any newer edition.
- [ ] data.ny.gov terms of use (link at the bottom of https://data.ny.gov) allow reuse with attribution. Note the wording in LICENSE if it asks for a specific credit line.

## Part 3: Check rows by hand (30 to 45 min)

For each: open the file, find the row, read the value, then confirm at the source.

**Five you know personally** (from `qa_report.txt` section 8, "known"):
- [ ] City of Albany 2019, revenues_total = [value]. Check in Open Book New York: https://www.openbooknewyork.com/ ___
- [ ] City of Troy 2019, revenues_total = [value]. Same site. ___
- [ ] Town of Colonie 2019, elec_mwh = [value]. Check at https://data.ny.gov/d/m3xm-q3dw, filter com_name Colonie, year 2019, Total Consumption, add the 12 months. ___
- [ ] Town of Bethlehem 2019, elec_mwh = [value]. Same method. ___
- [ ] Town of Red Hook: nypa_projects_cumulative in 2025 = [value]. Check at https://data.ny.gov/d/erjw-j2zx, filter customer containing Red Hook. ___

**Three extremes** (section 8, "max"):
- [ ] [entity, year, column = value]. Check at [link]. ___
- [ ] ...

**Five random rows** (section 8, seed 20261211):
- [ ] [entity, year, column = value]. Check at [link]. ___
- [ ] ...

## Part 4: Your decisions (10 min)

- [ ] **V1. Comptroller columns.** The pipeline reads revenue and expenditure from the section field [name found in the real file]. Totals for Albany 2019 should be close to Open Book's figure. Agree? ___
- [ ] **V2. Energy-relevant spending.** Counted: street lighting 5182, buildings 1620, water 8310 to 8350, sewer 8110 to 8130. Option A: keep as is (recommended). Option B: drop water and sewer, which carry much non-energy cost. Your choice: ___
- [ ] **V3. Towns and villages.** Does a UER town total include its villages? [Evidence from the real build: town versus village totals for Red Hook and two others.] Option A: treat towns as including villages and say so. Option B: report both as-is and warn users not to add them. Recommended: decide from the evidence. Your choice: ___
- [ ] **V5. Year alignment.** Keep fiscal-year finance beside calendar-year energy, documented in LIMITATIONS 2 (recommended for v0.1), or delay release to build fiscal-period energy. Your choice: ___

## Part 5: Before it goes public (15 to 30 min)

- [ ] The README "In plain terms" paragraph and the release description are in your own words. (Claude can do this with you line by line.)
- [ ] Name, ORCID, affiliation and email are correct in `AUTHORS.json` and `CITATION.cff`.
- [ ] You have read `docs/LIMITATIONS.md` and agree with it.
- [ ] Figures regenerated with `python code/04_figures.py --final`; README status line changed from DRAFT; `python tools/publish_gate.py . --allow-draft-in tools` passes.
- [ ] Evidence log row written on release day.

**When every box is ticked, tell Claude in your own words that you have checked the package and approve publishing.**
