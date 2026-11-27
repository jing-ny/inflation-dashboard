#!/usr/bin/env python3
"""Offline checks for the US "no annual rate" note (#132).

BLS has no October 2025 CPI, so it published no 12-month change for October
2026. index_months_without_yoy() finds such months so the record can say why
the series stopped, and merge_country_data() stores or clears the note.

    python3 scripts/test_yoy_gap.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_historical_cpi as f  # noqa: E402

FAILS = []
N = 0


def check(name, cond):
    global N
    N += 1
    print(("  ✅ " if cond else "  ❌ ") + name)
    if not cond:
        FAILS.append(name)


def index_obs(months, skip=()):
    """Monthly index observations, 100 rising 0.3 a month, minus `skip`."""
    out, v = [], 100.0
    for m in months:
        v += 0.3
        if m not in skip:
            out.append({"date": f"{m}-01", "value": round(v, 3)})
    return out


MONTHS = [f"{y}-{m:02d}" for y in (2024, 2025, 2026) for m in range(1, 13)][:34]  # to 2026-10

print("US October 2026")
obs = index_obs(MONTHS, skip={"2025-10"})
yoy = f.calculate_yoy_from_index(obs)
check("YoY ends at 2026-09 (October has no year-ago index)", yoy[-1]["date"] == "2026-09")
check("2026-10 also missing from the YoY series", "2026-10" not in {p["date"] for p in yoy})
gaps = f.index_months_without_yoy(obs, yoy[-1]["date"])
check("2026-10 reported as having no annual rate", [g["date"] for g in gaps] == ["2026-10"])
check("reason names the missing year-ago month", "2025-10" in gaps[0]["reason"])

print("No false notes")
obs = index_obs(MONTHS)
yoy = f.calculate_yoy_from_index(obs)
check("complete index: nothing reported", f.index_months_without_yoy(obs, yoy[-1]["date"]) == [])
rates = [{"date": f"{m}-01", "value": 2.0} for m in MONTHS]
check("YoY-rate source ending at its latest: nothing reported",
      f.index_months_without_yoy(rates, MONTHS[-1]) == [])
check("quarterly latest date: nothing reported",
      f.index_months_without_yoy(index_obs(MONTHS, skip={"2025-10"}), "2026-Q3") == [])
check("old gap behind the latest month is ignored",
      f.index_months_without_yoy(index_obs(MONTHS, skip={"2024-10"}), "2026-10") == [])
check("empty input", f.index_months_without_yoy([], "2026-09") == [])

print("merge_country_data")
f.fetch_us_supplementary = lambda existing: existing  # no network
existing = {"US": {"history": [{"date": "2026-08", "value": 3.4}, {"date": "2026-09", "value": 3.74}],
                   "latest": {"date": "2026-09", "value": 3.74}, "frequency": "monthly"}}
fetched = {"history": [{"date": "2026-08", "value": 3.4}, {"date": "2026-09", "value": 3.74}],
           "latest": {"date": "2026-09", "value": 3.74},
           "previous": {"date": "2026-08", "value": 3.4}, "fetched_from": "BLS",
           "yoy_unavailable": [{"date": "2026-10", "reason": "no index for 2025-10, so no annual rate"}]}
m = f.merge_country_data(existing, fetched, "US")
check("note stored on the record", m.get("yoy_unavailable", [{}])[0].get("date") == "2026-10")
gap = m["yoy_unavailable"][0]
check("note carries its source, source_url and fetch_date",
      gap.get("source") == "BLS" and gap.get("source_url", "").startswith("https://www.bls.gov")
      and len(gap.get("fetch_date", "")) == 10)
mf = f.merge_country_data({"US": dict(existing["US"])}, dict(fetched, fetched_from="FRED",
                          fred_series_used="CPIAUCNS"), "US")
check("FRED fallback is named as the source",
      mf["yoy_unavailable"][0]["source"] == "FRED"
      and mf["yoy_unavailable"][0]["source_url"].endswith("/CPIAUCNS"))
existing["US"] = m
m2 = f.merge_country_data(existing, dict(fetched, yoy_unavailable=[]), "US")
check("note cleared once nothing is unavailable", "yoy_unavailable" not in m2)
m3 = f.merge_country_data(existing, None, "US")
check("failed fetch keeps the note as it was", m3.get("yoy_unavailable") == m["yoy_unavailable"])

print(f"\n{'FAIL' if FAILS else 'OK'}: {N - len(FAILS)}/{N}")
sys.exit(1 if FAILS else 0)
