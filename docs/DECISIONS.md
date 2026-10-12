# Decision log

*Plain-language header: every judgment call made in building MUNI-BENCH, who made it, when, and why. Cite this file when someone asks why the data looks the way it does.*

| Date | ID | Decision | Made by | Basis |
|---|---|---|---|---|
| 2026-10-11 | D0 | Energy layer uses NYSERDA community-level data (city, town, village), not ZIP-level | Author | ZIP files cover two utilities only, with no 2021 data; community files cover all major utilities 2016 onward |
| 2026-10-12 | R1 | 19 NYPA review items: 16 accepted, 3 assigned (Putnam CSD to Putnam Central SD, Washington County; DeKalb Junction to Town of De Kalb; Tarrytown USFD to UFSD of the Tarrytowns) | Author | `docs/REVIEW_SUGGESTIONS.md`; assignments checked against NYPA project names and addresses on data.ny.gov |
| 2026-10-12 | V1 | Report revenue and expenditure totals both with and without other sources and uses (account codes 5000 to 5999 and 9900 to 9999) | Author, on Claude's recommendation | Comparisons need totals without borrowing and transfers. Correction, build 3: the Village of Red Hook 2019 gap that prompted this is not borrowing (other sources are about 65,000 of 5.18M); it is ordinary revenue. The decision stands on its general merit |
| 2026-10-12 | V1a | Section labels such as "STATEMENT OF REVENUES AND OTHER SOURCES" are classed by account code, not treated as other sources; where a government-year has rows under both label styles, statement rows that repeat short-label lines (90% or more) are dropped as copies, and every such case is logged | Claude, pipeline rule; for author confirmation after build 4 | Build 3 showed the file uses both label styles; prevents double counting |
| 2026-10-12 | V2 | Energy-relevant spending: street lighting 5182, buildings 1620, water 8310 to 8350, sewer 8110 to 8130 | Author | Recommended default |
| 2026-10-12 | V3 | Town and village relationship reported as unconfirmed; users told not to add them | Author | Account counts suggest towns may exclude villages, not tested statewide |
| 2026-10-12 | V5 | Fiscal-year finance beside calendar-year energy for v0.1 | Author | Fiscal-period alignment planned for v0.5 |
| 2026-10-12 | V6 | Community college projects out of scope | Author | Colleges are not OSC local governments |
| 2026-10-12 | V7 | Governments with no NYSERDA record carry no energy values; causes described generally | Author | 32 active governments; mostly municipal electric villages or town and village pairs sharing a boundary |
| 2026-10-12 | V8 | NYSERDA account allocation reported as published and flagged (Troy and Brunswick) | Author | MUNI-BENCH does not alter source values |
