#!/usr/bin/env python3
"""Offline checks for merge_into_main's commentary_date stamp (#129).

When a scraped report replaces a row's projections, the curated key_quote /
note still describe the older report. merge_into_main pins that text to its
report via ``commentary_date`` so the dashboard can label it (CLAUDE.md #4).

    python3 scripts/test_cb_commentary_date.py
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auto_scrape_cb_forecasts as cb  # noqa: E402

FAILS = []


def check(name, cond):
    print(("  ✅ " if cond else "  ❌ ") + name)
    if not cond:
        FAILS.append(name)


def run_merge(entry, fc):
    """Run merge_into_main in a temp cwd holding one-country cb_forecasts.json."""
    old = os.getcwd()
    tmp = tempfile.mkdtemp()
    try:
        os.chdir(tmp)
        os.makedirs("docs/data")
        with open("docs/data/cb_forecasts.json", "w") as f:
            json.dump({"metadata": {}, "forecasts": {"ZA": entry}}, f)
        merged, blocked = cb.merge_into_main([fc])
        with open("docs/data/cb_forecasts.json") as f:
            return merged, blocked, json.load(f)["forecasts"]["ZA"]
    finally:
        os.chdir(old)
        shutil.rmtree(tmp)


def za_entry(**extra):
    e = {"publication_date": "May 2026", "projections": {"2026": 4.4, "2027": 3.7},
         "key_quote": "Headline CPI seen averaging 4.4% in 2026", "note": "SARB hiked in May"}
    e.update(extra)
    return e


NOV = {"country": "ZA", "bank": "SARB", "source_date": "2026-11-01",
       "source_url": "https://example.invalid/2026/november/forecast.pdf",
       "projections": [{"year": "2026", "value": 4.3}, {"year": "2027", "value": 4.0}]}

print("merge_into_main commentary_date")
merged, _, e = run_merge(za_entry(), NOV)
check("newer report merges", len(merged) == 1)
check("projections replaced", e["projections"] == {"2026": 4.3, "2027": 4.0})
check("publication_date moves to November", e["publication_date"] == "November 2026")
check("commentary pinned to the May report", e.get("commentary_date") == "May 2026")
check("curated text kept as written", e["key_quote"].startswith("Headline CPI seen averaging 4.4%"))

_, _, e = run_merge(za_entry(), dict(NOV, source_date="2026-05-01"))
check("same report: no stamp", "commentary_date" not in e)

_, _, e = run_merge(za_entry(commentary_date="March 2026"), NOV)
check("existing stamp not moved forward", e["commentary_date"] == "March 2026")

_, _, e = run_merge(za_entry(key_quote="", note=""), NOV)
check("no curated text: no stamp", "commentary_date" not in e)

_, _, e = run_merge(za_entry(publication_date=None), NOV)
check("no previous publication: no stamp", "commentary_date" not in e)

blocked_fc = dict(NOV, projections=[{"year": "2026", "value": 6.0}])
merged, blocked, e = run_merge(za_entry(), blocked_fc)
check("gated step: nothing merged or stamped",
      not merged and blocked and "commentary_date" not in e and e["publication_date"] == "May 2026")

print(f"\n{'FAIL' if FAILS else 'OK'}: {10 - len(FAILS)}/10")
sys.exit(1 if FAILS else 0)
