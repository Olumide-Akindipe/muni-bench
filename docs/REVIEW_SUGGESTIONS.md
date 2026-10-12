# Review suggestions, build 2 (decided 2026-10-12)

*15 rows covering 19 NYPA project codes; rows 1, 2, 7 and 11 each cover two projects. All suggestions accepted by the maintainer.*

*Plain-language header: the NYPA projects the computer could not match with certainty. Each row shows NYPA's customer name, the proposed match, an AI-assisted suggestion and the reason. The maintainer decided each row; the decisions are in `data/review_decisions.csv`.*

Decisions: **accept** (proposed match is right), **reject** (leave unlinked), **assign** (link to the government named in the Target column).

| # | Project code(s) | NYPA customer (county) | Proposed match | Suggestion | Target | Reason |
|---|---|---|---|---|---|---|
| 1 | CH10015, ES-GSN-0831 | Briarcliff Public Schools (Westchester) | Briarcliff Manor UFSD | accept | | Only Comptroller school district named for Briarcliff |
| 2 | CH10316, CH10645 | Oyster Bay School (Nassau) | Oyster Bay-East Norwich CSD | accept | | Only district named for Oyster Bay |
| 3 | CH10441 | New Hyde / Garden City Park School (Nassau) | New Hyde Park-Garden City Park UFSD | accept | | Same district, abbreviated |
| 4 | CH10310 | Northport - East Northport School (Suffolk) | Northport-East Northport UFSD | accept | | Same district |
| 5 | CH10436 | Comsewogue CSD (Suffolk) | Brookhaven-Comsewogue UFSD | accept | | Comptroller's legal name for the Comsewogue district |
| 6 | CH10667 | Highland Falls CSD (Orange) | Highland Falls-Fort Montgomery SD | accept | | Same district, shortened |
| 7 | CH10655, ES-LIN-0009 | Patchogue School (Suffolk) | Patchogue-Medford UFSD | accept | | Same district, shortened |
| 8 | CH10785 | Allegany CSD (Cattaraugus) | Allegany-Limestone CSD | accept | | Only Comptroller school district named for Allegany in that county |
| 9 | CH10948 | Putnam CSD (NYPA says Putnam County) | Putnam Valley CSD (Putnam) | **assign** | 530769500100 | NYPA's address is Putnam Station, ZIP 12861, Washington County. This is Putnam Central School District; NYPA's county is wrong |
| 10 | CH11495 | Hastings Public Schools (Westchester) | Hastings-on-Hudson UFSD | accept | | Same district |
| 11 | ES-ESN-0217, ES-ESN-0911 | Jamestown BPU, City of (Chautauqua) | City of Jamestown | accept | | The Board of Public Utilities is the city's own utility department |
| 12 | ES-ESN-0609 | Plainview-Old Bethpage, Town of (Nassau) | Plainview-Old Bethpage CSD | accept | | NYPA's "Town of" label is wrong; no such town exists |
| 13 | ES-ESN-0846 | DeKalb Junction, Town of (St. Lawrence) | De Kalb Junction fire district | **assign** | 400322500000 | NYPA's project name is "Town of DeKalb - LED Street Lighting" (2021). The fire district stopped filing in 1999. Target is Town of De Kalb |
| 14 | ES-ESN-0827 | Perth, Town of (NYPA says Montgomery) | Town of Perth (Fulton) | accept | | Town of Perth is in Fulton County; NYPA's county is wrong |
| 15 | CH10591 | Tarrytown USFD (Westchester) | none (unmatched) | **assign** | 550634200100 | The Comptroller lists this district as "Union Free School District Of The Tarrytowns" |

Notes:
- Rows 1 to 8, 10 and 12 are school districts whose names NYPA shortened. Accepting them is the common case.
- Rows 9, 13 and 15 were checked against NYPA's own project address or name on data.ny.gov (2026-10-12).
- The NYSERDA energy links need no review in this build; every one is an exact match.
