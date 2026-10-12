#!/usr/bin/env python3
"""Make a small SYNTHETIC sample in the real source layouts, for testing code only.

Every number here is invented. Names are real New York places so the matching
logic is exercised realistically, but no value describes any real government.
"""
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
from muni import config as C  # noqa: E402

rng = random.Random(7)

# (municipal_code, OSC name, class, county, UER name, UER type, fips)
GOVS = [
    ("010101000000", "ALBANY", "City", "Albany", "Albany", "City", "3601000"),
    ("010102000000", "TROY", "City", "Rensselaer", "Troy", "City", "3675484"),
    ("010203000000", "COLONIE", "Town", "Albany", "Colonie", "Town", "3600117000"),
    ("010204000000", "BETHLEHEM", "Town", "Albany", "Bethlehem", "Town", "3600106000"),
    ("140301000000", "RED HOOK", "Town", "Dutchess", "Red Hook", "Town", "3602761027"),
    ("140302000000", "RED HOOK", "Village", "Dutchess", "Red Hook", "Village", "3661049"),
    ("350401000000", "SAINT JOHNSVILLE", "Village", "Montgomery", "St. Johnsville", "Village",
     "3664463"),
    ("020501000000", "GUILDERLAND", "Town", "Albany", "Guilderlnd", "Town", "3600131000"),
    ("010100000000", "ALBANY", "County", "Albany", None, None, None),
    ("010600000000", "BETHLEHEM CENTRAL SCHOOL DISTRICT", "School District", "Albany",
     None, None, None),
    ("990101000000", "NOWHERE", "Town", "Hamilton", None, None, None),
    # Edge cases found in the first real build:
    ("080352100000", "Town of Mc Donough", "Town", "Chenango", "McDonough", "Town", "3601744000"),
    ("550337700000", "Town of Harrison", "Town", "Westchester", "Harrison", "Town", "3632402"),
    ("550437702165", "Village of Harrison", "Village", "Westchester", "Harrison", "Village",
     "3632402"),
    ("040413302710", "Village of Limestone", "Village", "Cattaraugus", None, None, None),
    ("550673400100", "Rye Neck Union Free School District", "School District", "Westchester",
     None, None, None),
    ("170365400000", "Town of Perth", "Town", "Fulton", None, None, None),
    ("040701100100", "Allegany-Limestone Central School District", "School District",
     "Cattaraugus", None, None, None),
    ("280663400400", "Plainview-Old Bethpage Central School District", "School District",
     "Nassau", None, None, None),
]
GOVS += [
    ("560301000000", "Town of Arcade", "Town", "Wyoming", "Arcade", "Town", "3612102418"),
    ("560302000000", "Town of Attica", "Town", "Wyoming", "Attica", "Town", "3612103012"),
    ("550634200100", "Union Free School District Of The Tarrytowns", "School District",
     "Westchester", None, None, None),
    ("550434204850", "Village of Tarrytown", "Village", "Westchester", None, None, None),
]
# NYSERDA rows where a town's code carries the next town's name (seen in Wyoming County)
STRAY_NAME = {"3612102418": "Attica"}
UER_COUNTY = {"McDonough": "Chenang"}      # NYSERDA truncates county names
LAST_FY = {"040413302710": 2011}          # dissolved before the panel


def osc():
    rows = []
    for code, name, cls, county, *_ in GOVS:
        for y in range(2010, LAST_FY.get(code, 2025) + 1):
            base = rng.uniform(5e6, 9e7)
            for sec, acct, amt in [("REVENUE", "A1001", base), ("REVENUE", "A3005", base * .2),
                                   ("EXPENDITURE", "A1620.4", base * .05),
                                   ("EXPENDITURE", "A5182.4", base * .01),
                                   ("EXPENDITURE", "F8340.4", base * .03),
                                   ("EXPENDITURE", "A1010.1", base * .8),
                                   ("REVENUE", "A5710", base * .5),       # bond proceeds
                                   ("EXPENDITURE", "A9901.9", base * .02)]:  # transfer out
                rows.append({"CALENDAR_YEAR": y, "MUNICIPAL_CODE": code, "ENTITY_NAME": name,
                             "CLASS_DESCRIPTION": cls, "COUNTY": county,
                             "ACCOUNT_CODE": acct, "ACCOUNT_CODE_SECTION": sec,
                             "AMOUNT": round(amt, 2)})
    df = pd.DataFrame(rows)
    # Albany 2019: the same revenue lines repeated under a statement label (a copy)
    cp = df[(df.MUNICIPAL_CODE == "010101000000") & (df.CALENDAR_YEAR == 2019) &
            (df.ACCOUNT_CODE_SECTION == "REVENUE")].copy()
    cp["ACCOUNT_CODE_SECTION"] = "STATEMENT OF REVENUES AND OTHER SOURCES"
    # Troy 2019: statement-label lines that are NOT copies (different accounts)
    nc = df[(df.MUNICIPAL_CODE == "010102000000") & (df.CALENDAR_YEAR == 2019) &
            (df.ACCOUNT_CODE_SECTION == "REVENUE")].copy()
    nc["ACCOUNT_CODE_SECTION"] = "STATEMENT OF REVENUES AND OTHER SOURCES"
    nc["ACCOUNT_CODE"] = "A2701"
    return pd.concat([df, cp, nc], ignore_index=True)


def uer_community(years):
    rows = []
    for code, name, cls, county, uname, utype, fips in GOVS:
        if not uname:
            continue
        utils = ["National Grid"] + (["NYSEG"] if uname == "Colonie" else [])
        for y in years:
            for m in range(1, 13):
                for u in utils:
                    for dc, unit, field in [("electricity", "MWh", "3_nat_consumption"),
                                            ("natural_gas", "Therms", "6_nat_consumption")]:
                        val = round(rng.uniform(500, 50000), 2)
                        if uname == "St. Johnsville" and dc == "natural_gas" and m in (1, 2):
                            val = -999
                        if uname == "Bethlehem" and dc == "electricity" and y == 2017 and m == 3:
                            val = -500.0          # negative correction row
                        if uname == "Red Hook" and utype == "Village" and dc == "electricity" \
                                and y == 2019 and m == 5:
                            rows.append(dict(rows[-1], year=y, month=m, com_name=uname,
                                             com_type=utype, county_name=county,
                                             full_fips=fips + ".00", data_class=dc,
                                             data_field=field, unit=unit, value=10.0,
                                             utility_display_name=u))  # second piece
                        nm = STRAY_NAME.get(fips, uname) if (m == 1 and u == "National Grid") else uname
                        rows.append({"year": y, "month": m, "com_name": nm,
                                     "com_type": utype,
                                     "county_name": UER_COUNTY.get(uname, county),
                                     "full_fips": fips + ".00", "data_class": dc,
                                     "data_field": field,
                                     "data_field_display_name": "Total Consumption (T)",
                                     "unit": unit, "value": val,
                                     "number_of_accounts": rng.randint(100, 9000),
                                     "uer_id": 5, "data_stream": "community_monthly",
                                     "utility_display_name": u, "state_2": "NY"})
    return pd.DataFrame(rows)


def uer_zip(years):
    rows = []
    for z in ["12203", "12205", "12180"]:
        for y in years:
            for m in range(1, 13):
                rows.append({"year": y, "month": m, "zip_code": z, "zip_city": "x",
                             "data_class": "electricity", "data_field": "3_nat_consumption",
                             "data_field_display_name": "Total Consumption (T)",
                             "unit": "MWH", "value": round(rng.uniform(1e3, 9e3), 2),
                             "number_of_accounts": 100, "uer_id": 5,
                             "data_stream": "zipcode_monthly",
                             "utility_display_name": "National Grid", "state_2": "NY"})
    return pd.DataFrame(rows)


def nypa():
    custs = [("Town of Colonie", "Albany", None), ("City of Albany", "Albany", None),
             ("Albany County", "Albany", None), ("Bethlehem CSD", "Albany", None),
             ("Village of St. Johnsville", "Montgomery", None),
             ("City of New York", "New York", "DCAS"),
             ("NYS Office of General Services", "Albany", "OGS"),
             ("Town of Red Hook", "Dutchess", None), ("Village of Red Hook", "Dutchess", None),
             ("Town of Guilderlnd", "Albany", None), ("Town of Nowhereville", "Albany", None),
             ("NYCHA - NY City Housing Authority", "New York", None),
             ("SUFFOLK COUNTY COMMUNITY COLLEGE", "Suffolk", None),
             ("PERTH, TOWN OF", "Montgomery", None), ("ALLEGANY CSD", "Cattaraugus", None),
             ("PLAINVIEW-OLD BETHPAGE, TOWN OF", "Nassau", None),
             ("RYE NECK USFD", "Westchester", None), ("TARRYTOWN USFD", "Westchester", None)]
    rows = []
    for i in range(72):
        c, county, ag = custs[i % len(custs)]
        y = 1987 + (i * 13) % 40
        rows.append({"year_completed": y, "date_completed": f"{y}-06-30T00:00:00.000",
                     "project_code": f"P{i:04d}", "project_name": f"Project {i}",
                     "ny_state_county": county, "customer": c, "agency": ag or "",
                     "project_category": "Energy Efficiency",
                     "facility_description": "Office Buildings", "number_of_facilities": 1,
                     "total_project_cost": rng.randint(50_000, 5_000_000),
                     "electric_energy_reduction_kwh": rng.randint(10_000, 1_000_000),
                     "gas_savings_therms": rng.randint(0, 50_000),
                     "reduction_in_greenhouse_gas_emissions_tons": rng.randint(1, 900),
                     "zip": "12205", "state": "NY"})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    C.SAMPLE.mkdir(parents=True, exist_ok=True)
    osc().to_csv(C.SAMPLE / "osc_sample.csv", index=False)
    uer_community(range(2016, 2021)).to_csv(C.SAMPLE / "uer_community_2016_2020.csv", index=False)
    uer_community(range(2021, 2026)).to_csv(C.SAMPLE / "uer_community_2021_on.csv", index=False)
    uer_zip(range(2016, 2020)).to_csv(C.SAMPLE / "uer_zip_2016_2021.csv", index=False)
    nypa().to_csv(C.SAMPLE / "nypa_projects.csv", index=False)
    print("Synthetic sample written to data/sample/")
