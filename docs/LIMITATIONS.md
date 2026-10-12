# Limitations

*Plain-language header: what MUNI-BENCH cannot tell you and where its data is weak. Read before using or citing it. Every point here must stay true in anything written about the project.*

1. **Community energy is not government energy.** UER values are all electricity and gas consumed inside a city, town or village by homes, businesses and institutions. They do not measure the government's own buildings or streetlights. MUNI-BENCH supports comparisons of community context, not municipal operations.

2. **Fiscal years and calendar years differ.** OSC reports by fiscal year, which ends December 31 for towns and counties, May 31 for most villages, June 30 for school districts, and varies for cities. UER and NYPA values are calendar years. The panel aligns them by year label only.

3. **Privacy screening removes months.** NYSERDA withholds values that fail its privacy screen (reported as -999). A month counts only if every reporting utility gave a value; annual totals with fewer than 12 reported months are partial. Use `elec_months_reported` and `gas_months_reported` before comparing totals.

4. **NYSERDA's 2021-onward file has large monthly gaps.** For example, it has no rows at all for January to June 2021 for the City of Albany, and many places have only 6 months in 2022 and 2025. These are gaps in the source, not in the pipeline. `qa_report.txt` section 6 shows the average months reported per year. Compare full years only.

5. **Negative monthly values.** A small number of utility rows report negative consumption, likely billing corrections. Those months are excluded and counted in `*_months_invalid`.

6. **Account coverage and allocation vary.** Utilities assign accounts to communities, and some assignments look wrong. In 2019 the City of Troy carries about 7,778 electric accounts while the neighbouring, much smaller Town of Brunswick carries about 19,112, which suggests some Troy accounts are reported under Brunswick. MUNI-BENCH reports NYSERDA's values as published. Use `elec_accounts_avg` to judge whether a total plausibly covers a whole community.

7. **The ZIP-level energy data are incomplete.** Only Con Edison and National Grid report at ZIP level, Con Edison has no ZIP data for 2020 to 2022, National Grid has none for 2021, and no utility reports ZIP data for 2021. The ZIP table is a companion, not part of the panel.

8. **Utility coverage differs by protocol.** The 2016 to 2020 community file has no PSEG Long Island rows; Long Island communities have energy values from 2021 only. Villages served by their own municipal electric utility (for example Lake Placid, Tupper Lake, Greenport, Bath) appear to have no NYSERDA record, so they carry no energy values. Community choice aggregation may affect some values.

9. **Towns and villages may overlap.** Villages lie inside towns. Whether a NYSERDA town value includes the villages within it is not confirmed. Account counts suggest some town values cover only the area outside villages (for example, 2019: Town of Red Hook about 2,457 electric accounts, Village of Red Hook about 1,027, Village of Tivoli about 735), but this has not been tested statewide. Do not add town and village values together.

10. **Shared records.** Where a town and village share one boundary (for example Harrison and Woodbury), NYSERDA reports one record, linked to both governments and flagged `uer_shared_record`. Count it once.

11. **NYSERDA names are sometimes wrong; codes are used instead.** In Wyoming County, some rows carry the next town's name under a town's Census code (for example "Attica" on Arcade's code). The pipeline links by the code whose usual spelling matches, and records other candidate codes in `uer_alt_fips`.

12. **Name-based linkage can be wrong.** OSC, UER and NYPA share no common identifier. Links rely on normalized names, class and county. Exact matches are trusted; fuzzy matches are listed with scores and reviewed by the maintainer. Errors that survive review remain possible.

13. **NYPA scope.** Projects for state agencies, public authorities, New York City and its agencies (including NYCHA), community colleges, BOCES, cooperatives and private firms are not linked, because the OSC local government file does not cover those bodies. Their counts are in `qa_report.txt` section 4. NYPA savings are engineering estimates at completion, not measured results, and costs are nominal dollars.

14. **Counties, school districts and fire districts have no energy values in v0.1.** They carry finance and NYPA columns only.

15. **Energy-relevant expenditure is an approximation.** The function codes chosen (street lighting, buildings, water, sewer) contain non-energy spending. They indicate where energy costs sit, not energy cost itself.

16. **Revenue and spending totals include internal flows.** `revenues_total` and `expenditures_total` include borrowing proceeds and transfers between a government's own funds. Use `revenues_excl_other_sources` and `expenditures_excl_other_uses` to compare governments.

17. **Sources change.** All four sources are revised. Each release records the exact files used (PROVENANCE.txt) and is reproducible only against those files.
