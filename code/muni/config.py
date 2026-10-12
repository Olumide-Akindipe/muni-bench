"""Central configuration: source identifiers, paths, and analytic choices.

Plain-language header: this file lists where every source lives and the few
choices the pipeline makes (panel years, which accounts count as energy-related).
You only open it if you want to change one of those choices.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
SAMPLE = ROOT / "data" / "sample"
PAPER = ROOT / "paper"
FIGS = PAPER / "figures"

PANEL_START, PANEL_END = 2016, 2025

SOCRATA = "https://data.ny.gov/resource/{id}.csv"
SOCRATA_LANDING = "https://data.ny.gov/d/{id}"

# NYSERDA Utility Energy Registry, community (city/town/village) level
UER_COMMUNITY = {
    "uer_community_2016_2020": "m3xm-q3dw",
    "uer_community_2021_on": "4txm-py4p",
}
# NYSERDA Utility Energy Registry, ZIP level (companion table only)
UER_ZIP = {
    "uer_zip_2016_2021": "tzb9-c2c6",
    "uer_zip_2021_on": "g2x3-izm4",
}
NYPA = {"nypa_projects": "erjw-j2zx"}

# Only the total-consumption rows are needed; filtering at the server keeps
# downloads small. Matched on display name so both UER protocols are covered.
UER_TOTAL_FILTER = "data_field_display_name like 'Total Consumption%'"

OSC_FORM_URL = ("https://wwe1.osc.state.ny.us/localgov/findata/"
                "financial-data-for-local-governments.cfm")
OSC_DROP = RAW / "osc"   # the author saves the Comptroller zip or CSVs here

# OSC function codes treated as energy-relevant (decision V2, author, 2026-10-12).
# Codes follow the NYS Uniform System of Accounts.
ENERGY_FUNCTIONS = {
    "street_lighting": ["5182"],
    "buildings": ["1620"],
    "water": ["8310", "8320", "8330", "8340", "8350"],
    "sewer": ["8110", "8120", "8130"],
}

FUZZY_ACCEPT = 95   # score at or above: accepted automatically, still listed
FUZZY_REVIEW = 85   # score between REVIEW and ACCEPT: goes to the review queue
