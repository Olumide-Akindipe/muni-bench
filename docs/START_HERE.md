# Start Here: MUNI-BENCH

*Read this first. It explains your project in plain language. Terms are explained in [GLOSSARY.md](GLOSSARY.md).*

## What you are building

One free table where every New York city, town, village, county and school district has, for each year from 2016 to 2025, its finances, the electricity and gas used in its community, and the NYPA efficiency projects completed for it.

## Why it matters

A town board deciding whether to retrofit its buildings asks three things: what can we afford, how much energy are we dealing with, and what have similar towns already done. New York publishes all three answers, but in three places that do not talk to each other. The Comptroller calls a place "COLONIE", NYSERDA calls it "Colonie (Town)", and NYPA calls it "Town of Colonie". Nobody has joined them. MUNI-BENCH does that once, carefully, and publishes how every match was made, so anyone can compare governments without repeating the work.

Think of it as a phone book that finally lists each town's bank statement, utility bill and renovation history on the same page.

## Where the information comes from

All sources are free and public.

| Source | In plain terms | One row looks like | Link |
|---|---|---|---|
| NYS Comptroller, Financial Data for Local Governments | Every local government's annual money in and money out, reported to the state since 1995 | One government, one year, one budget line, one dollar amount | [form](https://wwe1.osc.state.ny.us/localgov/findata/financial-data-for-local-governments.cfm) |
| NYSERDA Utility Energy Registry, community level | Monthly electricity and gas used inside each city, town and village, reported by the utilities | One town, one month, one utility, megawatt-hours used | [2016 to 2020](https://data.ny.gov/d/m3xm-q3dw), [2021 on](https://data.ny.gov/d/4txm-py4p) |
| NYPA Energy Efficiency Completed Projects | Every public-facility efficiency project NYPA finished since 1987 | One project: customer, county, cost, estimated savings | [link](https://data.ny.gov/d/erjw-j2zx) |
| NYSERDA Utility Energy Registry, ZIP level (side table) | The same energy data by ZIP code, for two utilities only | One ZIP code, one month, one utility | [link](https://data.ny.gov/d/g2x3-izm4) |

## What you will have at the end

- [ ] **A public project page** on GitHub: github.com/Olumide-Akindipe/muni-bench
- [ ] **A permanent citation number (DOI)** from Zenodo, version 0.1.0, December 2026
- [ ] **The linked table** (`panel_2016_2025.csv`) plus the matching tables and a quality report
- [ ] **Two figures** for talks, the README and a later data paper

## How it connects to your work

Your proposed endeavor is a decision-support system for small and mid-sized municipalities' energy investments. Every such system needs a baseline: what each government spends, what its community uses, what has already been done. MUNI-BENCH is that baseline for New York, and it sits beside the Verification Gap Ledger, which tracks what the funding programs measure.

## Your one download (5 minutes)

The Comptroller site uses a form, so this file cannot be fetched automatically.

1. Open https://wwe1.osc.state.ny.us/localgov/findata/financial-data-for-local-governments.cfm
2. Under **Export Selection**, choose **Revenue, Expenditure and Balance Sheet Data**.
3. Under **Select Detail**, choose **All Classes of Government for All Years**.
4. Choose the **zipped .csv** option and click the export button. Save the zip.
5. Either put it in the folder `data/raw/osc/`, or attach it in our chat. Do not unzip or open it in Excel first; Excel can strip leading zeros from the government codes.

## What you need to do

| Your task | When | Time |
|---|---|---|
| Reply "community" or "ZIP only", and confirm your author details | Now | 2 min |
| Download the Comptroller zip (above) | Now | 5 min |
| Run the build (your computer or GitHub, see PUBLISH_GUIDE.md) | After the download | 20 min, mostly waiting |
| Decide the uncertain matches in `review_queue.csv` | After the build | 30 to 60 min |
| Check results with `VERIFY_CHECKLIST.md` | After the build | 1 to 2 hours |
| Approve publishing | After checking | 5 min |

## The steps ahead

1. **Pipeline written and tested.** Done, on made-up sample data.
2. **Data collected.** The real files are downloaded with receipts.
3. **Data cleaned and linked.** Governments matched across the three sources.
4. **Quality checks.** Counts, match rates, anything odd flagged.
5. **Your review and verification.** You rule on uncertain matches and check rows by hand.
6. **Publish.** GitHub release and Zenodo DOI.

*You are here: steps 1 to 5 complete (2026-10-12). Step 6, publish, is in docs/PUBLISH_GUIDE.md Parts C and D.*
