#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Offline tests for the NZ move to OECD SDMX (quarterly).

FRED's NZLCPIALLQINMEI relay stopped at 2026-Q1, which left NZ the one red
series on the freshness gate. NZ now reads OECD SDMX with freq="Q"
(NZL.Q.N.CPI.PA._T.N.GY), the same endpoint KR already uses monthly.

These tests pin:
  1. fetch_oecd_cpi_series(freq="Q") asks for the quarterly key and keeps only
     "YYYY-Qn" rows, so a stray monthly or annual row can't corrupt
     latest/previous; freq="M" (KR) is unchanged.
  2. A successful NZ fetch rebuilds the stored history wholesale, scrubbing the
     month-shaped duplicates ("2024-01", "2024-04", ...) and filling the gaps
     (2025-Q2, 2025-Q3) in the committed data.
  3. Quarters newer than what we had still go through the anomaly gate
     (CLAUDE.md #5); the backfilled archive does not.
  4. If OECD fails and the FRED fallback answers, history is NOT replaced, so
     a stale relay can't wipe newer points.

Self-contained: requests.get is stubbed, no network, no API key. It reads the
committed docs/data/historical_cpi.json but never writes it.

Run: python3 scripts/test_oecd_nz.py
"""

import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fetch_historical_cpi as f  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


class FakeResp:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def csv_body(rows):
    lines = ["DATAFLOW,REF_AREA,FREQ,TIME_PERIOD,OBS_VALUE"]
    lines += [f"OECD.SDD.TPS:DSD_PRICES@DF_PRICES_ALL(1.0),NZL,Q,{p},{v}" for p, v in rows]
    return "\n".join(lines) + "\n"


# Quarterly NZ rows as OECD returns them (2026-Q1..Q3 match what the live
# endpoint served on 2026-11-26: 3.079292, 4.058193, 3.714936), plus a stray
# monthly and an annual row that the quarterly filter must drop.
NZ_ROWS = [
    ("2025-Q1", "2.5"), ("2025-Q2", "2.7"), ("2025-Q3", "3.0"), ("2025-Q4", "3.1"),
    ("2026-Q1", "3.079292"), ("2026-Q2", "4.058193"), ("2026-Q3", "3.714936"),
    ("2026-06", "9.9"), ("2026", "9.9"),
]

calls = []


def fake_get(url, params=None, headers=None, timeout=None):
    calls.append(url)
    return FakeResp(csv_body(NZ_ROWS))


# --- 1. fetcher -------------------------------------------------------------
orig_get = f.requests.get
f.requests.get = fake_get
try:
    obs = f.fetch_oecd_cpi_series("NZL", "2016-Q1", "Q")
finally:
    f.requests.get = orig_get

check("quarterly key requested", calls and calls[-1].endswith("/NZL.Q.N.CPI.PA._T.N.GY"), calls[-1:])
check("only YYYY-Qn rows kept", [o["date"] for o in obs] == [p for p, _ in NZ_ROWS[:7]],
      [o["date"] for o in obs])

calls.clear()
f.requests.get = lambda url, **kw: (calls.append(url), FakeResp(
    "TIME_PERIOD,OBS_VALUE\n2026-09,2.88\n2026-Q3,9.9\n2026-10,2.82\n"))[1]
try:
    kr = f.fetch_oecd_cpi_series("KOR", "2026-01")
finally:
    f.requests.get = orig_get
check("monthly default unchanged (KR)", calls[-1].endswith("/KOR.M.N.CPI.PA._T.N.GY")
      and [o["date"] for o in kr] == ["2026-09", "2026-10"], [o["date"] for o in kr])

try:
    f.fetch_oecd_cpi_series("NZL", "2016-Q1", "A")
    check("unsupported frequency rejected", False)
except ValueError:
    check("unsupported frequency rejected", True)

# --- 2/3. fetch + merge against the committed data ---------------------------
with open(f.DATA_FILE, encoding="utf-8") as fh:
    existing = json.load(fh)
before = copy.deepcopy(existing["NZ"])

f.requests.get = fake_get
try:
    fetched = f.fetch_country_data("NZ")
finally:
    f.requests.get = orig_get

check("NZ fetched from OECD", fetched and fetched["fetched_from"] == "OECD", fetched and fetched.get("fetched_from"))
check("NZ asks for history rebuild", fetched and fetched.get("history_replace") is True)

f.ANOMALY_LOG.clear()
merged = f.merge_country_data(existing, copy.deepcopy(fetched), "NZ")
dates = [h["date"] for h in merged["history"]]
check("history is quarterly-only", all("-Q" in d for d in dates), [d for d in dates if "-Q" not in d])
check("gaps filled (2025-Q2, 2025-Q3)", "2025-Q2" in dates and "2025-Q3" in dates)
check("latest is 2026-Q3", merged["latest"]["date"] == "2026-Q3" and merged["latest"]["value"] == 3.71,
      merged["latest"])
check("previous is 2026-Q2", merged["previous"]["date"] == "2026-Q2", merged["previous"])
check("provenance on latest", merged["latest"].get("source") == "OECD"
      and "NZL.Q.N.CPI.PA._T.N.GY" in merged["latest"].get("source_url", "")
      and merged["latest"].get("fetch_date"), merged["latest"])
check("record source label is OECD", merged["source"] == "OECD")
check("no anomaly on real Q2/Q3 prints", not f.ANOMALY_LOG, f.ANOMALY_LOG)

# A new quarter that jumps >1pp still trips the gate.
f.ANOMALY_LOG.clear()
jump = copy.deepcopy(fetched)
jump["history"][-1] = {"date": "2026-Q3", "value": 6.0}
jump["latest"] = {"date": "2026-Q3", "value": 6.0}
f.merge_country_data(copy.deepcopy(existing), jump, "NZ")
check("new >1pp quarter is flagged", any(a["date"] == "2026-Q3" for a in f.ANOMALY_LOG), f.ANOMALY_LOG)
check("backfilled archive is not flagged", all(a["date"] > "2026-Q1" for a in f.ANOMALY_LOG), f.ANOMALY_LOG)
f.ANOMALY_LOG.clear()

# --- 4. FRED fallback must not replace history ------------------------------
def boom(*a, **kw):
    raise RuntimeError("OECD down")


orig_oecd, orig_fred = f.fetch_oecd_cpi_series, f.fetch_fred_series
f.fetch_oecd_cpi_series = boom
f.fetch_fred_series = lambda sid, start_date="2015-01-01": [
    {"date": "2025-01-01", "value": 100.0}, {"date": "2026-01-01", "value": 103.1}]
try:
    fb = f.fetch_country_data("NZ")
finally:
    f.fetch_oecd_cpi_series, f.fetch_fred_series = orig_oecd, orig_fred
check("FRED fallback does not rebuild history", fb and fb["fetched_from"] == "FRED"
      and not fb.get("history_replace"), fb)

print()
if FAILURES:
    print(f"{len(FAILURES)} failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("All OECD/NZ checks passed.")
