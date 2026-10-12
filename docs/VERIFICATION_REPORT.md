# MUNI-BENCH v0.1 verification report

*Plain-language header: this file records the hand checks that compare MUNI-BENCH values with the public sources they come from. Every number below can be found again on the source website or in the source file named next to it.*

| | |
|---|---|
| Dataset | MUNI-BENCH, linked panel 2016 to 2025 |
| Build checked | `muni-bench-build_3.zip` (GitHub Actions run, 2026-10-12): 32,640 panel rows, 33 columns, 12-digit municipal codes in every row, review queue empty, raw source files included |
| Checks performed by | Stephen Olumide Akindipe (author), 2026-10-12 |
| Account-level reconciliation | Computed from the author's Comptroller bulk file `all_classes_years.zip` (OSC snapshot date 2026-09-30) |
| Source versions | NYSERDA UER community files last updated 2026-10-06; NYPA projects file last updated 2026-07-27; Open Book New York accessed 2026-10-12 |
| Status | All sampled values reconciled. One pipeline addition approved (decision V1r) and pending implementation |

## 1. Summary

| Layer | Rows checked | Result |
|---|---|---|
| Energy (NYSERDA UER) | 5 government-years, both source files | 5 of 5 exact |
| NYPA projects | 3 governments | 3 of 3 exact |
| Linkage (UER codes) | 9 towns in Wyoming County, 2 shared records | All correct |
| Finance (OSC) against the bulk file | 12 government-years, revenue and expenditure | 24 of 24 exact |
| Finance (OSC) against Open Book | 12 government-years, revenue and expenditure | 24 of 24 reconciled to the dollar by a four-part rule (section 5) |

No sampled value in MUNI-BENCH differs from its source. The finance checks found that MUNI-BENCH totals and Open Book totals are defined differently; the difference is fully explained and is addressed by decision V1r.

## 2. Method

1. Rows were taken from `VERIFY_CHECKLIST.md` Part 3: places known to the author, the largest values in the panel, five random rows (seed 20261211), and the Wyoming County linkage fix. Colonie 2019 finance and Village of Red Hook 2025 finance were added as extra rows.
2. Energy: the author exported the NYSERDA community file from data.ny.gov, filtered to the community, community type, year, `data_class` electricity and `data_field_display_name` "Total Consumption (T)", and summed the monthly values.
3. NYPA: the author searched the NYPA completed projects file on data.ny.gov by customer name.
4. Finance: the author opened the Open Book New York Trend report (Revenues and Expenditures) for each government and year. Claude then summed the same government-year in the Comptroller bulk file by account code to explain every difference.
5. Panel values were read from the build files listed above.

## 3. Energy

Source: NYSERDA Utility Energy Registry, Monthly Community Energy Use. 2016 to 2020: data.ny.gov `m3xm-q3dw`. 2021 onward: data.ny.gov `4txm-py4p`.

| Government and year | Panel `elec_mwh` | Source sum (MWh) | Accounts (panel / source) | Months | Result |
|---|---|---|---|---|---|
| City of Albany 2019 | 1,189,663.666 | 1,189,663.68 | 41,418 / 41,417.9 | 12 | Exact |
| Town of Colonie 2019 | 669,921.119 | 669,921.12 | 29,539 / 29,539 | 12 | Exact |
| Town of Bethlehem 2019 | 591,294.741 | 591,294.74 | 14,540 / 14,540 | 12 | Exact |
| City of Buffalo 2018 (panel maximum) | 2,786,511.734 | 2,786,511.734 | 120,218 / 120,218 | 12 | Exact |
| Village of Alexandria Bay 2025 | 12,787.5 | 12,787.50 | 847 / not recorded | 12 | Exact |

Notes:
- Bethlehem's electricity use is high relative to Colonie. The account count (14,540) fits the town's size, so the record is Bethlehem's own and the higher use per account is in the source.
- The author's first Albany sum (1,190,770.98) came from an export that also held Cohoes, Watervliet and 13 other measures. Recounting the same export filtered to Albany and "Total Consumption (T)" gave the exact value.

## 4. NYPA projects and linkage

Source: NYPA Energy Efficiency Completed Projects: Beginning 1987, data.ny.gov `erjw-j2zx`.

| Check | Panel | Source | Result |
|---|---|---|---|
| City of Syracuse 2021, `nypa_cost` (largest single-year cost) | 29,843,184.16; 1 project | ES-ESN-0725, City of Syracuse LED Street Lighting, completed 2021-03-01, $29,843,184 | Exact |
| Town of Red Hook 2025, `nypa_projects_cumulative` | 1 (0 completed in 2025) | ES-ESN-0686, Town of Red Hook LED Street Lighting, completed 2021-03-29, $247,406; no other Town project | Exact |
| Red Hook Central School District | 1 project (2024) | ES-ESN-0871, Red Hook CSD Solar PV, three sites, $1,696,489 | Linked to the school district, not the town |

The same name search returned seven projects in the Red Hook neighbourhood of Brooklyn (NYC DEP, NYC Parks, NYCHA). These are New York City projects and are correctly outside the panel's scope.

Linkage, `link_uer.csv`:

| Check | Result |
|---|---|
| Towns of Arcade, Attica, Bennington, Eagle, Gainesville, Java, Middlebury, Sheldon (Wyoming County) | Each links to its own NYSERDA code. The neighbouring code that carries a stray copy of the town's name in NYSERDA's file is listed as the rejected alternative (for example, Attica links to 3612103012 and rejects Arcade's code 3612102418) |
| Harrison, Woodbury | Town and village share one NYSERDA record, as expected for governments with a shared boundary |

## 5. Finance

Source: NYS Office of the State Comptroller, Financial Data for Local Governments (bulk file) and Open Book New York (Trend report, Revenues and Expenditures).

### 5.1 Panel against the Comptroller bulk file

For all 12 government-years, `revenues_total` and `expenditures_total` equal the sums of the REVENUE and EXPENDITURE sections of the bulk file. The pipeline reads and sums the source correctly.

### 5.2 Bulk file against Open Book

Open Book's totals ("Revenues and Proceeds of Debt"; "Expenditures") equal the bulk-file section totals minus four components:

1. Interfund transfers: lines in the "Other Sources" and "Other Uses" categories (transfers between a government's own funds).
2. Custodial funds: fund prefix `TC` (money held for others).
3. Private-purpose trust funds: fund prefix `TE`.
4. Escrow payments for refunding bonds: account narrative "Repayments to Escrow Agent for Advance Refunding Bonds" (for example `V99914`), which carries no spending category in the bulk file.

Proceeds of Debt remain in Open Book's revenue total.

| Government and year | Fiscal period | Side | Panel (bulk) | Transfers | Custodial TC | Trust TE | Escrow | Rule result | Open Book |
|---|---|---|---|---|---|---|---|---|---|
| Meadowmere Fire District 2018 | Jan to Dec 2018 | Rev | 737,008 | 0 | 0 | 0 | 0 | 737,008 | 737,008 |
| | | Exp | 470,884 | 0 | 0 | 0 | 0 | 470,884 | 470,884 |
| City of Albany 2019 | Jan to Dec 2019 | Rev | 210,651,694 | 280,577 | 0 | 0 | 0 | 210,371,117 | 210,371,117 |
| | | Exp | 203,716,579 | 280,577 | 0 | 0 | 0 | 203,436,002 | 203,436,002 |
| Town of Bethlehem 2019 | Jan to Dec 2019 | Rev | 67,384,459 | 2,498,472 | 0 | 0 | 0 | 64,885,987 | 64,885,987 |
| | | Exp | 60,699,350 | 2,498,471 | 0 | 0 | 0 | 58,200,879 | 58,200,879 |
| Town of Colonie 2019 | Jan to Dec 2019 | Rev | 118,326,879 | 2,000,000 | 0 | 487,106 | 0 | 115,839,773 | 115,839,773 |
| | | Exp | 126,380,330 | 2,000,000 | 0 | 287,526 | 0 | 124,092,804 | 124,092,804 |
| Village of Red Hook 2019 | Jun 2018 to May 2019 | Rev | 5,175,993 | 65,000 | 0 | 0 | 0 | 5,110,993 | 5,110,993 |
| | | Exp | 2,845,500 | 65,000 | 0 | 0 | 0 | 2,780,500 | 2,780,500 |
| Village of Red Hook 2025 | Jun 2024 to May 2025 | Rev | 5,966,112 | 45,234 | 0 | 18,286 | 0 | 5,902,593 | 5,902,593 |
| | | Exp | 4,829,015 | 45,234 | 0 | 20,802 | 0 | 4,762,979 | 4,762,979 |
| Town of Red Hook 2025 | Jan to Dec 2025 | Rev | 9,437,553 | 667,689 | 0 | 0 | 0 | 8,769,864 | 8,769,864 |
| | | Exp | 8,476,507 | 667,689 | 0 | 0 | 0 | 7,808,818 | 7,808,818 |
| Village of Alexandria Bay 2025 | Jun 2024 to May 2025 | Rev | 5,733,492 | 352,029 | 0 | 0 | 0 | 5,381,463 | 5,381,463 |
| | | Exp | 4,220,819 | 352,029 | 0 | 0 | 0 | 3,868,790 | 3,868,790 |
| Marathon CSD 2020 | Jul 2019 to Jun 2020 | Rev | 18,783,353 | 189,155 | 0 | 11,980 | 0 | 18,582,218 | 18,582,218 |
| | | Exp | 22,591,064 | 189,155 | 0 | 12,640 | 0 | 22,389,269 | 22,389,269 |
| Williamson CSD 2023 | Jul 2022 to Jun 2023 | Rev | 33,670,030 | 574,542 | 530,913 | 48,873 | 0 | 32,515,702 | 32,515,702 |
| | | Exp | 30,639,848 | 574,542 | 520,019 | 31,850 | 0 | 29,513,437 | 29,513,437 |
| County of Wyoming 2022 | Jan to Dec 2022 | Rev | 182,928,913 | 17,083,068 | 760,479 | 0 | 0 | 165,085,366 | 165,085,366 |
| | | Exp | 186,884,227 | 17,083,068 | 835,613 | 0 | 0 | 168,965,547 | 168,965,547 |
| County of Nassau 2021 | Jan to Dec 2021 | Rev | 6,339,278,000 | 605,715,000 | 392,685,000 | 0 | 0 | 5,340,878,000 | 5,340,878,000 |
| | | Exp | 5,859,773,000 | 605,715,000 | 392,685,000 | 0 | 1,283,618,000 | 3,577,755,000 | 3,577,755,000 |

Bethlehem's expenditure transfers differ from revenue transfers by 1 dollar of rounding in the source.

### 5.3 Size of each component statewide

Bulk file, all classes, fiscal years 2016 to 2025:

| Component | Share of gross revenue | Share of gross expenditure |
|---|---|---|
| Fiduciary funds (TC, TE) | 8.25% | 8.41% |
| Interfund transfers | 5.28% | 5.39% |
| Proceeds of Debt | 4.89% | not applicable |
| Escrow payments for refunding bonds | not applicable | 0.75% |

The escrow line is the only expenditure line without a spending category in these years (695 lines). The existing `revenues_excl_other_sources` column removes transfers and Proceeds of Debt together (10.2% of revenue), which matches the figure in the build 4 notes.

### 5.4 Village of Red Hook 2019 surplus

The village reported revenues of 5,110,993 against expenditures of 2,780,500 in Open Book. The account-level Open Book report shows State Aid of 2,713,007, of which 2,214,238 (EW3989) went to the water fund and 462,500 (ES3901) to the sewer fund, with no Proceeds of Debt. The water and sewer funds are enterprise funds, which report depreciation (EW19944, 313,305) rather than capital outlay. The surplus is a state grant recorded as revenue in the year received, with the work it funds expensed over later years. It does not reflect borrowing or a pipeline error.

## 6. Decisions taken from these checks

Recorded in the decision log on 2026-10-12.

| ID | Decision |
|---|---|
| V1r | Keep `revenues_total`, `expenditures_total` and the existing excl columns. Add `revenues_openbook` and `expenditures_openbook` using the rule in section 5.2, and component columns `proceeds_of_debt`, `transfers_in`, `transfers_out`, `fiduciary_rev`, `fiduciary_exp`, `refunding_escrow`. Replaces V1, whose basis (borrowing in Red Hook's revenue) was ruled out |
| V3r | NYSERDA town records cover the town outside its incorporated villages, including hamlets. Kept as published. A whole-town figure is the town row plus its village rows |
| S1 | Scope option (a): all OSC classes kept, including fire districts. QUESTION line in the build spec widened |

## 7. Documentation changes required

| File | Change |
|---|---|
| `CODEBOOK.md` | Define the V1r columns. State the year convention: year is the fiscal year in which the period ends (January to December for cities, towns, counties and fire districts; June to May for villages; July to June for school districts); energy is calendar year. State that NYPA records include renewables such as solar PV. Add the V3r town and village rule |
| `LIMITATIONS.md` | Add: water and sewer enterprise funds (EW, ES) report depreciation rather than capital outlay, so energy-relevant water and sewer spending is understated for those governments in grant years. Add: in refunding years Open Book totals include bond proceeds in revenue but exclude the matching escrow payment from expenditure |
| `VERIFY_CHECKLIST.md` | Use the exact label "Total Consumption (T)" and filter `com_name` and `com_type`. Replace the Open Book address with https://www.osc.ny.gov/open-book-new-york and name the Trend report. Describe `nypa_projects_cumulative` as cumulative since 1987 |

## 8. Limits of this verification

- The sample covers 12 finance government-years, 5 energy government-years and 3 NYPA governments. It confirms the pipeline logic and the Open Book rule on those rows. It is not a statewide audit.
- Open Book values were read from the author's screen captures and one PDF. The bulk file is a snapshot dated 2026-09-30; OSC revises local government data quarterly for five years, so recent years (2025 in particular) may change.
- The V1r columns do not exist yet. After they are added, the next build's QA report should show `revenues_openbook` and `expenditures_openbook` equal to the Open Book values in section 5.2 for all 12 government-years.

## 9. Open items before release

1. Implement V1r in the pipeline and rebuild.
2. Confirm the QA report reproduces the 24 Open Book totals in section 5.2.
3. Apply the documentation changes in section 7.
4. Check the GitHub workflow folder holds only the current workflow file.