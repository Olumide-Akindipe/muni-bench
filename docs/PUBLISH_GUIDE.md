# Publish guide: MUNI-BENCH v0.1.0

*Plain-language header: the exact clicks to put MUNI-BENCH on GitHub, run the build, and get the DOI. Parts A and B are done. Parts C and D publish the release. No GitHub or Zenodo token was supplied, so these steps are yours; each takes a few minutes.*

## Copy-ready text

**Repository name:** `muni-bench`

**Title:** MUNI-BENCH: Entity-Level Linkage of New York Local Government Finance, Community Energy Use, and Public-Facility Efficiency Projects

**Author:** Stephen Olumide Akindipe (ORCID 0000-0002-1846-9662), Independent Researcher, Albany, NY, USA

**Keywords:** municipal finance; energy use; energy efficiency; New York State; local government; Utility Energy Registry; panel data

**Short description (for GitHub "About" and Zenodo):** MUNI-BENCH is an open entity-year panel for 2016 to 2025 connecting New York local government finances (State Comptroller), community electricity and gas use (NYSERDA Utility Energy Registry), and completed NYPA public-facility efficiency projects, with documented match methods, to give energy planners, municipal stakeholders, researchers and the public easy access to linked information.

## Part A. Put the code on GitHub (10 minutes)

1. Go to https://github.com/new. Owner: Olumide-Akindipe. Name: `muni-bench`. Public. Leave "Add a README" unticked. Click **Create repository**.
2. Download the project zip from our chat and unzip it.
3. On the new repository page, click **uploading an existing file**. Drag in everything from inside the unzipped `muni-bench` folder, including the hidden `.github` and `.gitignore` (on a Mac press Cmd+Shift+. to show them; on Windows tick View > Hidden items). Commit message: `Initial pipeline`. Click **Commit changes**.
   You should now see README.md shown below the file list.

## Part B. Run the real build on GitHub (10 minutes of clicks, about 30 minutes of waiting)

1. Download the Comptroller zip (docs/START_HERE.md, "Your one download").
2. In the repository: **Releases** (right side) > **Draft a new release**. Click **Choose a tag**, type `osc-input`, click **Create new tag**. Title: `Comptroller input file`. Drag the Comptroller zip into the attachments box. Tick **Set as a pre-release**. Click **Publish release**.
3. Click the **Actions** tab. If asked, click **I understand my workflows, go ahead and enable them**.
4. Click **build-muni-bench** on the left, then **Run workflow** > **Run workflow**.
5. When the run shows a green tick, open it and download **muni-bench-build** at the bottom.
6. Attach that zip in our chat. I will read the quality report with you and fill in the checklist with real rows.

If the run shows a red cross, attach a screenshot of the failed step; the most likely cause is a column name in the Comptroller file (verify point V1), which is a one-line fix.

## Part C. Connect Zenodo (3 minutes, once)

1. Go to https://zenodo.org/account/settings/github/ (log in with GitHub).
2. Find `Olumide-Akindipe/muni-bench` and flip its switch to **On**.
   Do this before Part D, or the release will not get a DOI. The `osc-input` pre-release is not archived.

## Part D. Release v0.1.0 (after verification only, 10 minutes)

1. Confirm every box in `docs/VERIFY_CHECKLIST.md` is ticked and `python tools/publish_gate.py . --allow-draft-in tools code docs/GLOSSARY.md docs/VERIFY_CHECKLIST.md` passes.
2. Releases > **Draft a new release**. Tag: `v0.1.0`. Title: `MUNI-BENCH v0.1.0`. Notes: your short description, plus "First public release. See docs/LIMITATIONS.md."
3. Attach `data/processed` as a zip so the tables travel with the DOI.
4. Click **Publish release**. Within a few minutes Zenodo emails you the DOI.
5. On the Zenodo record, click **Edit** and check: creator is Stephen Olumide Akindipe with ORCID; license CC BY 4.0; keywords as above. Save.
6. Copy the DOI into `CITATION.cff`, the README status line and Citation section, and your evidence log, the same day.

## Evidence log row (fill on release day)

```
date,artifact_or_event,type,venue_or_host,link_or_doi,status,prong_tags,metrics_snapshot,files_saved,notes
2026-10-12,MUNI-BENCH v0.1.0 release (code archive),software,Zenodo + GitHub,10.5281/zenodo.23314418 (concept 10.5281/zenodo.23314416),live,"P1, P2",0 downloads at release,release_page.pdf; zenodo_record.pdf,First public release after verification
```

Save a PDF of the GitHub release page and the Zenodo record that day. Publications not logged the day they happen are the ones that go missing at petition time.

## Part E. v0.1.1: put the data inside the DOI (2026-10-12)

Zenodo's GitHub link archives only the repository, not files attached to a release, so v0.1.0's DOI holds the code only. v0.1.1 commits the verified tables to the repository and adds `.zenodo.json`, which tells Zenodo the resource type is Dataset.

Evidence log row for v0.1.1 (add the version DOI from the Zenodo record):
```
2026-10-12,MUNI-BENCH v0.1.1 release (data archive),dataset,Zenodo + GitHub,[v0.1.1 version DOI] (concept 10.5281/zenodo.23314416),live,"P1, P2",0 downloads at release,release_page.pdf; zenodo_record.pdf,Adds verified data files; values identical to v0.1.0 build
```
