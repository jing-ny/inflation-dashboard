#!/usr/bin/env python3
"""Offline checks for the BoE Table 3.B parser and its merge (#10).

NOV_2026 is the text pdfplumber extracted from Table 3.B of the November 2026
Monetary Policy Report (pp. 75-76), copied from a dry-run log. APR_2026_SHAPE
is a hand-built table in the April 2026 "Summary of scenarios" layout, using
the values the curated UK entry carries, to keep the old path working.

    python3 scripts/test_boe_table_3b.py
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auto_scrape_cb_forecasts as cb  # noqa: E402

FAILS = []
N = 0


def check(name, cond):
    global N
    N += 1
    print(("  ✅ " if cond else "  ❌ ") + name)
    if not cond:
        FAILS.append(name)


NOV_2026 = [
    'Bank of England Page 75',
    'Table 3.B: Summary of outputs of the central projection and scenarios (a)',
    '2026 Q4 2027 Q4 2028 Q4 2029 Q4',
    'Central projection',
    'CPI inflation (b) 3.8 (3.2) 4.0 (2.1) 2.0 (1.9) 1.8',
    'GDP (c) 2.2 (1.2) 1.0 (1.4) 1.4 (1.7) 1.6',
    'Excess supply/excess demand (d) -1.0 (-1.3) -1.2 (-0.9) -1.3 (-0.7) -1.1',
    'Unemployment rate (e) 4.8 (5.1) 5.0 (5.3) 5.1 (5.2) 5.0',
    'Private sector regular average weekly earnings (f) 3.2 (3.0) 3.5 (3.1) 3.4 (3.1) 3.1',
    'Energy prices – direct contribution to CPI inflation (g) 1.1 (0.4) 0.3 (-0.1) -0.5 (-0.2) 0.0',
    'World export prices (h) 8.0 (4.3) 1.2 (0.5) -0.7 (-0.2) -0.7',
    'Bank Rate (i) 3.9 (3.9) 4.9 (4.2) 4.9 (4.1) 4.7',
    'Adverse inflation scenario',
    'CPI inflation (b) 4.0 5.5 3.0 2.2',
    'GDP (c) 2.2 0.8 1.3 1.6',
    'Excess supply/excess demand (d) -1.1 -1.4 -1.5 -1.4',
    'Unemployment rate (e) 4.8 5.1 5.3 5.1',
    'Private sector regular average weekly earnings (f) 3.5 4.5 4.6 4.1',
    'Energy prices – direct contribution to CPI inflation (g) 1.2 1.1 -0.5 -0.3',
    'World export prices (h) 8.8 3.5 0.0 -0.7',
    'Bank Rate (i) 3.9 4.9 4.9 4.7',
    'Weaker demand scenario',
    'CPI inflation (b) 3.8 3.6 1.2 1.2',
    'GDP (c) 2.2 0.3 1.3 1.6',
    'Excess supply/excess demand (d) -1.0 -1.8 -1.7 -1.6',
    'Unemployment rate (e) 4.8 5.3 5.5 5.3',
    'Private sector regular average weekly earnings (f) 3.2 2.8 2.2 2.0',
    'Bank of England Page 76',
    '2026 Q4 2027 Q4 2028 Q4 2029 Q4',
    'Energy prices – direct contribution to CPI inflation (g) 1.1 0.3 -0.5 0.0',
    'World export prices (h) 8.0 1.2 -0.7 -0.7',
    'Bank Rate (i) 3.9 4.9 4.9 4.7',
    '(a) The numbers shown in this table are conditioned on the assumptions described in Table 3.A and the Projections',
    'Databank accompanying this Report. All three scenarios are conditioned on the same market curve for Bank Rate. The',
    'numbers in parentheses show the equivalent projections at the time of the July 2026 Monetary Policy Report.',
]

PROSE_BEFORE = [
    "Contents",
    "3.2: Central projection and scenarios 72",
    "Table 3.B sets out how key economic variables evolve across the central projection and",
    "the CPI inflation (b) 9.9 9.9 9.9 9.9 figure quoted in prose must never be read",
]

PROSE_AFTER = [
    "Chart 3.2: CPI inflation in the central projection is expected to return to the 2% target",
    "Central projection",
    "In the central projection, conditioned on the market curve for interest rates, CPI inflation is",
]

APR_2026_SHAPE = [
    "Table 3.B: Summary of scenarios",
    "2026 Q2 2027 Q2 2028 Q2 2029 Q2",
    "Scenario A",
    "CPI inflation (a) 3.1 2.9 1.5 1.7",
    "GDP (b) 1.0 1.2 1.4 1.5",
    "Scenario B",
    "CPI inflation (a) 3.1 3.2 2.0 2.0",
    "Scenario C",
    "CPI inflation (a) 3.6 5.6 2.9 2.6",
]

print("November 2026 layout")
years, paths, central = cb._parse_boe_table_3b(PROSE_BEFORE + NOV_2026 + PROSE_AFTER)
check("year columns read", years == ["2026", "2027", "2028", "2029"])
check("central projection found", central == "Central projection")
check("central CPI path, July values in parentheses stripped",
      paths.get("Central projection") == {"2026": 3.8, "2027": 4.0, "2028": 2.0, "2029": 1.8})
check("adverse scenario",
      paths.get("Adverse inflation scenario") == {"2026": 4.0, "2027": 5.5, "2028": 3.0, "2029": 2.2})
check("weaker demand scenario",
      paths.get("Weaker demand scenario") == {"2026": 3.8, "2027": 3.6, "2028": 1.2, "2029": 1.2})
check("exactly three paths (energy-contribution rows ignored)", len(paths) == 3)

print("April 2026 layout")
years, paths, central = cb._parse_boe_table_3b(APR_2026_SHAPE)
check("no central projection", central is None)
check("scenarios A/B/C keep their letter names", sorted(paths) == ["A", "B", "C"])
check("scenario C path", paths["C"] == {"2026": 3.6, "2027": 5.6, "2028": 2.9, "2029": 2.6})

print("Unreadable table")
years, paths, central = cb._parse_boe_table_3b(PROSE_BEFORE + PROSE_AFTER)
check("prose only: nothing parsed", not paths and central is None)
one = [l for l in NOV_2026 if "Adverse" not in l and "Weaker" not in l]
one = one[:one.index("Bank Rate (i) 3.9 (3.9) 4.9 (4.2) 4.9 (4.1) 4.7") + 1]
years, paths, central = cb._parse_boe_table_3b(one)
check("central projection alone is enough", central == "Central projection" and len(paths) == 1)
no_central_row = [l for l in NOV_2026 if l != "CPI inflation (b) 3.8 (3.2) 4.0 (2.1) 2.0 (1.9) 1.8"]
years, paths, central = cb._parse_boe_table_3b(no_central_row)
check("central label but no CPI row: nothing, not a scenario-only range",
      not paths and central is None)
split = list(NOV_2026)
k = split.index("Weaker demand scenario")
split[k:k] = ["Table 3.B (continued)"]
years, paths, central = cb._parse_boe_table_3b(split)
check("'Table 3.B (continued)' header doesn't cut the table",
      "Weaker demand scenario" in paths and central == "Central projection")
years, paths, central = cb._parse_boe_table_3b(APR_2026_SHAPE + PROSE_AFTER)
check("April table followed by a 'Central projection' prose heading still parses",
      sorted(paths) == ["A", "B", "C"] and central is None)
years, paths, central = cb._parse_boe_table_3b(
    ["Table 3.B: Summary of outputs of the central projection and scenarios (a)"]
    + no_central_row[1:] + ["Contents"] + APR_2026_SHAPE)
check("an unreadable region doesn't stop the search", sorted(paths) == ["A", "B", "C"])
years, paths, central = cb._parse_boe_table_3b(
    NOV_2026 + ["Table 3.C: Something else", "Scenario Z", "CPI inflation (a) 9.0 9.0 9.0 9.0"])
check("the next table is not read", "Z" not in paths)


def run_merge(entry, fc):
    old = os.getcwd()
    tmp = tempfile.mkdtemp()
    try:
        os.chdir(tmp)
        os.makedirs("docs/data")
        with open("docs/data/cb_forecasts.json", "w") as f:
            json.dump({"metadata": {}, "forecasts": {"UK": entry}}, f)
        merged, blocked = cb.merge_into_main([fc])
        with open("docs/data/cb_forecasts.json") as f:
            return merged, blocked, json.load(f)["forecasts"]["UK"]
    finally:
        os.chdir(old)
        shutil.rmtree(tmp)


print("Merge of a central projection over the April scenario row")
april_entry = {
    "publication_date": "April 2026", "forecast_type": "CPI inflation (MPC scenario range)",
    "projections": {"2026": 3.35, "2027": 4.25, "2028": 2.2, "2029": 2.15},
    "projection_range": {"2026": [3.1, 3.6], "2027": [2.9, 5.6]},
    "scenarios": {"A": {"2026": 3.1}, "B": {"2026": 3.1}, "C": {"2026": 3.6}},
    "key_quote": "curated April text", "note": "curated April note",
}
years, paths, central = cb._parse_boe_table_3b(NOV_2026)
fc = {
    "country": "UK", "bank": "Bank of England", "source_date": "2026-11-01",
    "source_url": "https://example.invalid/monetary-policy-report-november-2026.pdf",
    "metric": "CPI inflation, Q4 four-quarter rate (MPC central projection)",
    "scenarios": paths, "central_scenario": central,
    "projections": [{"year": y, "value": paths[central][y]} for y in years],
}
merged, blocked, e = run_merge(april_entry, fc)
check("merges (largest step 0.45pp, inside the 1pp gate)", len(merged) == 1 and not blocked)
check("projections are the central path", e["projections"] == paths[central])
check("April range dropped, so pages show the point values", "projection_range" not in e)
check("central_scenario recorded", e.get("central_scenario") == "Central projection")
check("forecast_type follows the source", e["forecast_type"].endswith("(MPC central projection)"))
check("all three paths kept for the country page", len(e["scenarios"]) == 3)

print(f"\n{'FAIL' if FAILS else 'OK'}: {N - len(FAILS)}/{N}")
sys.exit(1 if FAILS else 0)
