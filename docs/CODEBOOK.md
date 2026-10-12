# Codebook

*Plain-language header: every column in every output table, what it means, where it came from, and how it was computed. Open it when you want to know what a column is. DRAFT until the first real build confirms the source fields.*

## panel_2016_2025.csv (one row per OSC entity per year, 2016 to 2025)

| Column | Meaning | Source and transformation |
|---|---|---|
| municipal_code | OSC identifier for the local government | OSC, as reported (text; keep leading zeros) |
| entity_name | Government name as OSC spells it | OSC, latest year reported |
| class | city, town, village, county, school district, fire district | OSC class label, normalized |
| county | County as OSC reports it | OSC |
| year | Fiscal year label in OSC data; calendar year for energy and NYPA columns | See LIMITATIONS 2 |
| revenues_total | Sum of all revenue lines, dollars | OSC, sum of AMOUNT where section is revenue [VERIFY V1] |
| expenditures_total | Sum of all expenditure lines, dollars | OSC, sum of AMOUNT where section is expenditure |
| exp_street_lighting | Expenditure in function 5182, dollars | OSC account code, first four digits [VERIFY V2] |
| exp_buildings | Expenditure in function 1620, dollars | as above |
| exp_water | Expenditure in functions 8310 to 8350, dollars | as above |
| exp_sewer | Expenditure in functions 8110 to 8130, dollars | as above |
| has_finance | True if OSC reported revenue or expenditure for that year | derived |
| uer_fips | Census code of the linked UER community | UER full_fips, trailing ".00" removed |
| uer_link_method | exact, fuzzy_auto, or fuzzy_review+author_accept | link_uer.csv |
| uer_shared_record | True when one NYSERDA record is linked to two governments (a town and village sharing one boundary, e.g. Harrison, Woodbury). Never add their energy values together | derived |
| elec_mwh | Community electricity use in the calendar year, MWh, summed over utilities and over complete months | UER, "Total Consumption (T)", unit MWh |
| elec_months_reported | Months (0 to 12) where every reporting utility gave a value | derived |
| elec_months_withheld | Months where at least one utility's value was withheld for privacy (-999) | derived |
| elec_months_invalid | Months where a utility reported a negative value (not the -999 privacy code); excluded from elec_mwh | derived |
| elec_accounts_avg | Average monthly number of electric accounts behind elec_mwh, over reported months, rounded | UER number_of_accounts, summed over utilities |
| gas_therms, gas_months_reported, gas_months_withheld, gas_months_invalid, gas_accounts_avg | Same for natural gas, therms | UER, unit Therms |
| nypa_projects | NYPA projects completed that calendar year for this entity | NYPA, linked via link_nypa.csv |
| nypa_cost | Sum of total_project_cost, dollars (nominal) | NYPA |
| nypa_kwh_savings | Sum of estimated annual electric savings, kWh | NYPA electric_energy_reduction_kwh |
| nypa_therm_savings | Sum of estimated annual gas savings, therms | NYPA gas_savings_therms |
| nypa_ghg_tons | Sum of estimated CO2 reduction, tons | NYPA reduction_in_greenhouse_gas_emissions_tons |
| nypa_projects_cumulative | Projects completed from 1987 through this year | NYPA |

## entities.csv
One row per OSC entity: municipal_code, entity_name, class (as reported), class_n (normalized), county, first_fy, last_fy.

## link_uer.csv
One row per OSC city, town or village: municipal_code, uer_fips, uer_com_name, method (exact, fuzzy_auto, fuzzy_review, unmatched, not_in_panel_years for governments whose last OSC filing is before 2016, with "+author_accept" or "+author_reject" after your review), score (0 to 100 name similarity), uer_alt_fips (other NYSERDA codes carrying the same place, not used), accepted (True if used in the panel).

Matching rules: same class of government; county compatible, allowing for NYSERDA's truncated ("Jeffers"), joint ("Broome & Delaware") and blank county names; name equal after normalization or after removing spaces ("Mc Donough" and "McDonough").

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

Review-only matches enter the panel only after you accept them.

## review_queue.csv
Uncertain matches for the maintainer: source (uer or nypa), record_id, method, left (the name being matched, with NYPA's county), right (the proposed match, with its class and county), score, decision (blank). Copy decided rows into `data/review_decisions.csv` with columns source, record_id, decision (accept or reject).

## community_energy_annual.csv
One row per UER community per calendar year, all years available (not limited to linked entities): fips, year, elec_mwh, elec_months_reported, elec_months_withheld, gas_therms, gas_months_reported, gas_months_withheld.

## zip_energy_annual.csv (companion)
One row per ZIP code, energy type and calendar year: zip_code, data_class, year, total, months_reported, months_withheld. Con Edison and National Grid territory only, with year gaps (see LIMITATIONS 7).

## uer_communities.csv
One row per NYSERDA community code and class: fips, com_type_n, com_name (most common spelling), name_variants (every spelling seen), counties (as NYSERDA wrote them), first_year, last_year, n_rows.
