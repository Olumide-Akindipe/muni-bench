# Limitations

*Plain-language header: what MUNI-BENCH cannot tell you and where its data is weak. Read before using or citing it. Every point here must stay true in anything written about the project.*

1. **Community energy is not government energy.** UER values are all electricity and gas consumed inside a city, town or village by homes, businesses and institutions. They do not measure the government's own buildings or streetlights. MUNI-BENCH supports comparisons of community context, not municipal operations.

2. **Fiscal years and calendar years differ.** OSC reports by fiscal year, which ends December 31 for towns and counties, May 31 for most villages, June 30 for school districts, and varies for cities. UER and NYPA values are calendar years. The panel aligns them by year label only.

3. **Privacy screening removes months.** NYSERDA withholds values that fail its privacy screen (reported as -999). A month counts only if every reporting utility gave a value; annual totals with fewer than 12 reported months are partial. Use `elec_months_reported` and `gas_months_reported` before comparing totals.

4. **The ZIP-level energy data are incomplete.** Only Con Edison and National Grid report at ZIP level, Con Edison has no ZIP data for 2020 to 2022, National Grid has none for 2021, and no utility reports ZIP data for 2021. The ZIP table is a companion, not part of the panel.

5. **Utility coverage differs by protocol.** The 2016 to 2020 community file has no PSEG Long Island rows; Long Island communities have energy values from 2021 only. Municipal electric utilities and community choice aggregators may be missing or partial.

6. **Towns and villages may overlap.** Villages lie inside towns. Whether a UER town value includes the villages within it is not yet confirmed [VERIFY V3]. Do not add town and village values together until this is settled.

7. **Name-based linkage can be wrong.** OSC, UER and NYPA share no common identifier. Links rely on normalized names, class and county. Exact matches are trusted; fuzzy matches are listed with scores and reviewed by the maintainer. Errors that survive review remain possible.

8. **NYPA scope.** Projects for state agencies, public authorities and New York City agencies are not linked, because the OSC local government file does not cover those entities. NYPA savings are engineering estimates at completion, not measured results, and costs are nominal dollars.

9. **Counties, school districts and fire districts have no energy values in v0.1.** They carry finance and NYPA columns only.

10. **Energy-relevant expenditure is an approximation.** The function codes chosen (street lighting, buildings, water, sewer) contain non-energy spending. They indicate where energy costs sit, not energy cost itself [VERIFY V2].

11. **Sources change.** All four sources are revised. Each release records the exact files used (PROVENANCE.txt) and is reproducible only against those files.
