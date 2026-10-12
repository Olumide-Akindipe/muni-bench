# Talking about MUNI-BENCH

*DRAFT. Numbers in brackets are filled from paper/stats.json after the real build and your verification. Claim nothing beyond what is here.*

## 60-second version

The problem: a town deciding on an energy investment needs to know what it can afford, what energy its community uses, and what similar places have already done. New York publishes all three, but in three systems that use different names and no common ID, so nobody compares them.

What I built: MUNI-BENCH, an open dataset that links the State Comptroller's local government finances, NYSERDA's community energy registry, and NYPA's record of 2,942 completed public-facility efficiency projects into one table, one row per government per year from 2016 to 2025. Every link records how it was made, and uncertain links were reviewed by hand.

What it makes possible: side-by-side comparison of [n] local governments on spending, community energy use and efficiency project history, without each analyst rebuilding the matches.

Who can use it: municipal energy managers, regional planning boards, NYSERDA and NYPA program staff, and researchers.

Where it is: GitHub (Olumide-Akindipe/muni-bench), DOI [DOI].

## Two-sentence version

MUNI-BENCH is an open dataset linking New York local government finances, community energy use and NYPA efficiency projects for [n] governments, 2016 to 2025. It gives municipal energy planning a documented, reusable baseline.

## Questions you may be asked

1. **Where does the data come from?** Three public state sources: the Comptroller's local finance data, NYSERDA's Utility Energy Registry, and NYPA's completed projects list, all downloaded with recorded fingerprints so anyone can rebuild the table.
2. **What are its limits?** The energy figures cover the whole community, not the government's own buildings; finance is by fiscal year while energy is by calendar year; some months are withheld for privacy; and matching by name can err, which is why every match is labeled and the uncertain ones were reviewed.
3. **Why does this matter beyond New York?** Most states publish similar finance, utility and program data separately. MUNI-BENCH shows a documented way to join them, which is the data foundation a municipal energy decision-support system needs.
