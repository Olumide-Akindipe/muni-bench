# Talking about MUNI-BENCH

*Every number here comes from paper/stats.json (build of 2026-10-12), verified by the maintainer. Claim nothing beyond what is here.*

## 60-second version

The problem: a town deciding on an energy investment needs to know what it can afford, what energy its community uses, and what similar places have already done. New York publishes all three, but in three systems that use different names and no common ID, so nobody compares them.

What I built: MUNI-BENCH, an open dataset that links the State Comptroller's local government finances, NYSERDA's community energy registry, and NYPA's record of 2,942 completed public-facility efficiency projects into one table, one row per government per year from 2016 to 2025. Every link records how it was made; 19 uncertain project links were reviewed by hand, and the build checks itself for errors in the source files.

What it makes possible: side-by-side comparison of 3,264 local governments on spending, and of 1,504 cities, towns and villages on community energy use, alongside NYPA efficiency project history for 391 governments, without each analyst rebuilding the matches.

Who can use it: municipal energy managers, regional planning boards, NYSERDA and NYPA program staff, and researchers.

Where it is: GitHub (Olumide-Akindipe/muni-bench) and Zenodo, with a permanent DOI.

## Two-sentence version

MUNI-BENCH is an open dataset linking New York local government finances, community energy use and NYPA efficiency projects for 3,264 governments, 2016 to 2025. It gives municipal energy planning a documented, reusable baseline.

## Questions you may be asked

1. **Where does the data come from?** Three public state sources: the Comptroller's local finance data, NYSERDA's Utility Energy Registry, and NYPA's completed projects list, all downloaded with recorded fingerprints so anyone can rebuild the table.
2. **What are its limits?** The energy figures cover the whole community, not the government's own buildings; finance is by fiscal year while energy is by calendar year; some months are withheld for privacy; and matching by name can err, which is why every match is labeled and the uncertain ones were reviewed.
3. **Why does this matter beyond New York?** Most states publish similar finance, utility and program data separately. MUNI-BENCH shows a documented way to join them, which is the data foundation a municipal energy decision-support system needs.
