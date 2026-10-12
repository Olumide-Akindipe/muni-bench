# Codebook

*Plain-language header: every column in every output table, what it means, where it came from, and how it was computed. Open it when you want to know what a column is.*

## panel_2016_2025.csv (one row per OSC entity per year, 2016 to 2025)

| Column | Meaning | Source and transformation |
|---|---|---|
| municipal_code | OSC identifier for the local government | OSC, as reported (text; keep leading zeros) |
| entity_name | Government name as OSC spells it | OSC, latest year reported |
| class | city, town, village, county, school district, fire district | OSC class label, normalized |
| county | County as OSC reports it | OSC |
| year | Year label. Finance: the Comptroller's fiscal year, labelled by the calendar year in which it ends (towns, cities, counties, fire districts: January to December Y; most villages: June Y-1 to May Y; school districts: July Y-1 to June Y), as in Open Book New York. Energy and NYPA: calendar year Y | See LIMITATIONS 2 |
| revenues_total | Gross revenues: sum of every line in the Comptroller's revenue section, dollars. Rebuild check: revenues_openbook + transfers_in + fiduciary_rev = revenues_total | OSC, sum of AMOUNT where the section is revenue or other sources |
| revenues_excl_other_sources | Revenues without other sources (borrowing proceeds, interfund transfers in). Use this to compare governments | as above, excluding account codes 5000 to 5999 (and any section labelled only "Other Sources") |
| expenditures_total | Gross expenditures: sum of every line in the expenditure section, dollars. Rebuild check: expenditures_openbook + transfers_out + fiduciary_exp + refunding_escrow = expenditures_total | OSC, sum of AMOUNT where the section is expenditure or other uses |
| revenues_openbook | Revenues as Open Book New York reports them ("Revenues and Proceeds of Debt"): gross revenues minus interfund transfers in and fiduciary (TC, TE) revenue. Proceeds of debt stay in | decision V1r; docs/VERIFICATION_REPORT.md section 5.2 |
| expenditures_openbook | Expenditures as Open Book New York reports them: gross expenditures minus interfund transfers out, fiduciary (TC, TE) expenditure and escrow payments for refunding bonds | decision V1r |
| proceeds_of_debt | Revenue lines in the proceeds-of-debt category (not fiduciary, not transfers). Included in revenues_openbook; lets users net out borrowing, including refunding years | OSC LEVEL_1/LEVEL_2 category |
| transfers_in, transfers_out | Interfund transfers: category Other Sources (revenue) or Other Uses (expenditure), subcategory Transfers, outside fiduciary funds | OSC LEVEL_1/LEVEL_2 category |
| fiduciary_rev, fiduciary_exp | Lines in custodial (fund prefix TC) and private-purpose trust (TE) funds, money held for others | account code prefix |
| refunding_escrow | Expenditure lines paying an escrow agent for advance refunding bonds (for example V99914), outside fiduciary funds and transfers | account code narrative |
| expenditures_excl_other_uses | Expenditures without other uses (interfund transfers out) | as above, excluding account codes 9900 to 9999 (and any section labelled only "Other Uses") |
| exp_street_lighting | Expenditure in function 5182, dollars | OSC account code, first four digits |
| exp_buildings | Expenditure in function 1620, dollars | as above |
| exp_water | Expenditure in functions 8310 to 8350, dollars | as above |
| exp_sewer | Expenditure in functions 8110 to 8130, dollars | as above |
| has_finance | True if OSC reported revenue or expenditure for that year | derived |
| uer_fips | Census code of the linked UER community | UER full_fips, trailing ".00" removed |
| uer_link_method | exact, fuzzy_auto, or fuzzy_review+author_accept | link_uer.csv |
| uer_fips (towns) | A NYSERDA town record covers the town outside its incorporated villages, including hamlets (decision V3r). For a whole-town figure, add the town row to its village rows | decision V3r |
| uer_shared_record | True when one NYSERDA record is linked to two governments (a town and village sharing one boundary, e.g. Harrison, Woodbury). Never add their energy values together | derived |
| elec_mwh | Community electricity use in the calendar year, MWh, summed over utilities and over complete months | UER, "Total Consumption (T)", unit MWh |
| elec_months_reported | Months (0 to 12) where every reporting utility gave a value | derived |
| elec_months_withheld | Months where at least one utility's value was withheld for privacy (-999) | derived |
| elec_months_invalid | Months where a utility reported a negative value (not the -999 privacy code); excluded from elec_mwh | derived |
| elec_accounts_avg | Average monthly number of electric accounts behind elec_mwh, over reported months, rounded | UER number_of_accounts, summed over utilities |
| gas_therms, gas_months_reported, gas_months_withheld, gas_months_invalid, gas_accounts_avg | Same for natural gas, therms | UER, unit Therms |
| nypa_projects | NYPA projects completed that calendar year for this entity. NYPA's register includes renewable energy projects (for example solar PV) as well as efficiency projects | NYPA, linked via link_nypa.csv |
| nypa_cost | Sum of total_project_cost, dollars (nominal) | NYPA |
| nypa_kwh_savings | Sum of estimated annual electric savings, kWh | NYPA electric_energy_reduction_kwh |
| nypa_therm_savings | Sum of estimated annual gas savings, therms | NYPA gas_savings_therms |
| nypa_ghg_tons | Sum of estimated CO2 reduction, tons | NYPA reduction_in_greenhouse_gas_emissions_tons |
| nypa_projects_cumulative | Projects completed from 1987 through this year | NYPA |

## entities.csv
One row per OSC entity: municipal_code, entity_name, class (as reported), class_n (normalized), county, first_fy, last_fy.

## link_uer.csv
One row per OSC city, town or village: municipal_code, uer_fips, uer_com_name, method (exact, fuzzy_auto, fuzzy_review, unmatched, not_in_panel_years for governments whose last OSC filing is before 2016, variant_review when only a stray spelling on some NYSERDA rows matches, with "+author_accept" or "+author_reject" after your review), score (0 to 100 name similarity), uer_alt_fips (other NYSERDA codes carrying the same place, not used), accepted (True if used in the panel).

Matching rules: same class of government; county compatible, allowing for NYSERDA's truncated ("Jeffers"), joint ("Broome & Delaware") and blank county names; name equal after normalization or after removing spaces ("Mc Donough" and "McDonough"). When several codes carry the name, the code whose usual spelling is this name wins, then a truncated spelling ("Centre Isl"), then the most data.

## link_nypa.csv
One row per NYPA project: project_code, customer, customer_class (inferred from the name), county, municipal_code, entity_name, method, score, accepted.

Methods, in the order tried:
- not_in_scope_nyc: City of New York, its agencies, and NYCHA.
- not_in_scope_state: state agencies, SUNY, CUNY, MTA, Port Authority, and similar.
- not_in_scope_other: bodies that do not file as OSC local governments: community colleges, BOCES, housing, transit and water authorities, cooperatives, libraries, universities, private firms.
- exact: same name, class and county. Accepted.
- fuzzy_auto: near-identical spelling (score 95 or more), same class and county. Accepted.
- fuzzy_review: close spelling (85 to 94). Review only.
- partial_review: NYPA's name is a shortened form ("Allegany CSD" for Allegany-Limestone CSD). Review only.
- other_county_review: same name and class, but NYPA lists a different county. Review only.
- class_mismatch_review: same county, but NYPA's class label disagrees ("Plainview-Old Bethpage, Town of" is a school district). Review only.
- unmatched.

Review-only matches enter the panel only after you accept them. Your decisions add "+author_accept", "+author_reject" or "+author_assign" to the method.

## review_queue.csv
Uncertain matches for the maintainer: source (uer or nypa), record_id, method, left (the name being matched, with NYPA's county), right (the proposed match, with its class and county), score, decision (blank). Decisions go in `data/review_decisions.csv` with columns source, record_id, decision (accept, reject or assign) and target (for assign: the OSC municipal_code for NYPA rows, the NYSERDA fips for UER rows).

## community_energy_annual.csv
One row per UER community per calendar year, all years available (not limited to linked entities): fips, year, elec_mwh, elec_months_reported, elec_months_withheld, gas_therms, gas_months_reported, gas_months_withheld.

## zip_energy_annual.csv (companion)
One row per ZIP code, energy type and calendar year: zip_code, data_class, year, total, months_reported, months_withheld. Con Edison and National Grid territory only, with year gaps (see LIMITATIONS 7).

## uer_communities.csv
One row per NYSERDA community code and class: fips, com_type_n, com_name (most common spelling), name_variants (every spelling seen), counties (as NYSERDA wrote them), first_year, last_year, n_rows.

## osc_label_overlap.csv
One row per government, year and kind (revenue or expenditure) that has rows under both of the Comptroller's label styles ("REVENUE" and "STATEMENT OF REVENUES AND OTHER SOURCES", and the expenditure equivalents): line counts and amounts under each, the share of statement lines that repeat a short-label line, and the action taken (statement_dropped_as_copy when 90% or more repeat, otherwise both_kept).

## osc_families_by_year.csv
Rows, amounts and number of governments under each label style, by kind, class of government and year, 2016 to 2025.

## osc_sections.csv
Every Comptroller section label found, how the pipeline classed it (revenue or expenditure), its row count, and how many rows count as other sources or uses. Lets anyone confirm decision V1 against the source file.

## osc_other_by_code.csv
Other sources and uses, 2016 to 2025, summed by government, year, kind and the first two digits of the account code.

## osc_uncategorized_lines.csv
Expenditure lines, 2016 to 2025, with no spending category that are not refunding escrow payments. The maintainer's statewide check found none; any listed here are kept in expenditures_openbook and need review.

## data/hand_checks.csv (input)
The maintainer's Open Book New York figures for 12 government-years, checked 2026-10-12. Each build compares revenues_openbook, expenditures_openbook and proceeds_of_debt with them and reports the gaps in `qa_report.txt` section 2.
