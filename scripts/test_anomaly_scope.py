#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Offline tests: the "exactly matches prior-year same period" anomaly check runs
only for text/PDF-parsed sources (#125).

The 2026-11-23 update-data run fetched UK 2026-10 = 3.6% from the ONS API
(d7g7). UK Oct 2025 was also 3.6%, so the prior-year check fired, the script
exited 2 and nothing from that run was committed (UK, ZA, JP and SG updates
lost). The check was added for the BR/MX miscapture, where press-release
comparison text was stored as the current reading; a structured ONS series
can't do that.

Pins:
  1. UK 2026-10 = 3.6% from ONS merges with no anomaly.
  2. The step check still fires for a structured source.
  3. A StatsSA (PDF) value equal to last year's is still flagged.
  4. A StatsSA row that actually came from the FRED fallback is not.

Self-contained: reads the committed docs/data/historical_cpi.json, writes
nothing, makes no network calls.

Run: python3 scripts/test_anomaly_scope.py
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


with open(f.DATA_FILE, encoding="utf-8") as fh:
    existing = json.load(fh)


def merge(code, point, fetched_from):
    f.ANOMALY_LOG.clear()
    fetched = {
        "history": [dict(point)],
        "latest": dict(point),
        "fetched_from": fetched_from,
    }
    # Keep the test about anomaly scope, not US supplementary refreshes.
    f.merge_country_data(copy.deepcopy(existing), fetched, code)
    return list(f.ANOMALY_LOG)


def prior_year(code, date):
    return f._prior_year_value(existing[code]["history"], date)


# 1. the real 2026-11-23 case
uk_prior = prior_year("UK", "2026-10")
check("fixture: UK 2025-10 is 3.6", uk_prior == 3.6, uk_prior)
log = merge("UK", {"date": "2026-10", "value": 3.6}, "ONS")
check("UK 2026-10 = 3.6 from ONS is not an anomaly", not log, log)

# 2. step check unaffected for structured sources
log = merge("UK", {"date": "2026-10", "value": 5.0}, "ONS")
check("step >1pp from ONS still flagged", any("step" in r for a in log for r in a["reasons"]), log)

# 3. text-parsed source keeps the prior-year check
za_last = max(h["date"] for h in existing["ZA"]["history"] if "-Q" not in h["date"])
y, m = za_last.split("-")
nxt = f"{int(y) + (m == '12')}-{1 if m == '12' else int(m) + 1:02d}"
za_prior = prior_year("ZA", nxt)
if za_prior is None:
    # The committed ZA history has gaps; plant last year's point so the
    # check has something to match.
    za_prior = 4.4
    existing["ZA"]["history"].append({"date": f"{int(nxt[:4]) - 1}{nxt[4:]}", "value": za_prior})
if True:
    log = merge("ZA", {"date": nxt, "value": za_prior}, "Stats SA")
    check("StatsSA value equal to prior year is flagged",
          any("prior-year" in r for a in log for r in a["reasons"]), log)
    # 4. ...unless it came from the FRED fallback
    log = merge("ZA", {"date": nxt, "value": za_prior}, "FRED")
    check("ZA via FRED fallback skips the prior-year check",
          not any("prior-year" in r for a in log for r in a["reasons"]), log)

f.ANOMALY_LOG.clear()
print()
if FAILURES:
    print(f"{len(FAILURES)} failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("All anomaly-scope checks passed.")
