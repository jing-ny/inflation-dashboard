#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Offline tests: the "exactly matches prior-year same period" anomaly check is
skipped only for structured, period-keyed sources (#125).

The 2026-11-23 update-data run fetched UK 2026-10 = 3.6% from the ONS API
(d7g7). UK Oct 2025 was also 3.6%, so the prior-year check fired, the script
exited 2 and nothing from that run was committed. The check exists for the
BR/MX miscapture (press-release comparison text stored as the current
reading), which a structured series can't produce.

Pins:
  1. UK 2026-10 = 3.6% from ONS merges with no anomaly.
  2. The step check still fires for a structured source.
  3. Text-parsed rows (Stats SA PDF, NBS release) keep the prior-year check.
  4. EA's provisional Eurostat flash (scraped HTML) keeps it on an ECB row.
  5. A text-parsed row that actually came from the FRED fallback skips it.
  6. A fetcher not in STRUCTURED_APIS is checked by default.
  7. The history_replace rebuild path follows the same rule.

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
    COMMITTED = json.load(fh)


def next_month(date):
    y, m = int(date[:4]), int(date[5:7])
    return f"{y + (m == 12)}-{1 if m == 12 else m + 1:02d}"


def setup(code, prior_value):
    """Committed data, plus a prior-year point for the month after `code`'s
    latest monthly point, so the prior-year match has something to hit."""
    data = copy.deepcopy(COMMITTED)
    months = [h["date"] for h in data[code]["history"] if "-Q" not in h["date"]]
    new_date = next_month(max(months))
    prior_date = f"{int(new_date[:4]) - 1}{new_date[4:]}"
    hist = [h for h in data[code]["history"] if h["date"] != prior_date]
    hist.append({"date": prior_date, "value": prior_value})
    data[code]["history"] = hist
    return data, new_date


def reasons(code, point, fetched_from, data, **extra):
    f.ANOMALY_LOG.clear()
    fetched = {"history": [dict(point)], "latest": dict(point), "fetched_from": fetched_from}
    fetched.update(extra)
    f.merge_country_data(data, fetched, code)
    out = [r for a in f.ANOMALY_LOG for r in a["reasons"]]
    f.ANOMALY_LOG.clear()
    return out


def has_prior_year(rs):
    return any("prior-year" in r for r in rs)


# 1. the real 2026-11-23 case, on the committed data as it stands
check("fixture: committed UK 2025-10 is 3.6",
      f._prior_year_value(COMMITTED["UK"]["history"], "2026-10") == 3.6)
rs = reasons("UK", {"date": "2026-10", "value": 3.6}, "ONS", copy.deepcopy(COMMITTED))
check("UK 2026-10 = 3.6 from ONS is not an anomaly", not rs, rs)

# 2. step check unaffected
rs = reasons("UK", {"date": "2026-10", "value": 5.0}, "ONS", copy.deepcopy(COMMITTED))
check("step >1pp from ONS still flagged", any("step" in r for r in rs), rs)

# 3. text-parsed rows keep the check
for code, label in [("ZA", "Stats SA"), ("CN", "NBS")]:
    latest = [h for h in COMMITTED[code]["history"] if "-Q" not in h["date"]]
    last_val = sorted(latest, key=lambda h: h["date"])[-1]["value"]
    data, d = setup(code, last_val)  # equal to latest too, so no step reason
    rs = reasons(code, {"date": d, "value": last_val}, COMMITTED[code].get("source", label), data)
    check(f"{code} ({label}) value equal to prior year is flagged", has_prior_year(rs), rs)

    # 5. ...unless the row actually came from the FRED fallback
    data, d = setup(code, last_val)
    rs = reasons(code, {"date": d, "value": last_val}, "FRED", data)
    check(f"{code} via FRED fallback skips the prior-year check", not has_prior_year(rs), rs)

# 4. EA flash: provisional point on a structured (ECB) row keeps the check
ea_last = sorted((h for h in COMMITTED["EA"]["history"] if "-Q" not in h["date"]),
                 key=lambda h: h["date"])[-1]["value"]
data, d = setup("EA", ea_last)
rs = reasons("EA", {"date": d, "value": ea_last, "provisional": True}, "ECB", data)
check("EA provisional flash equal to prior year is flagged", has_prior_year(rs), rs)
data, d = setup("EA", ea_last)
rs = reasons("EA", {"date": d, "value": ea_last}, "ECB", data)
check("EA final from the ECB API skips the prior-year check", not has_prior_year(rs), rs)

# 6. fails closed: a fetcher not on the structured list is checked
orig_api = f.COUNTRIES["UK"]["api"]
f.COUNTRIES["UK"]["api"] = "SomeNewPDFScraper"
try:
    rs = reasons("UK", {"date": "2026-10", "value": 3.6}, "ONS", copy.deepcopy(COMMITTED))
finally:
    f.COUNTRIES["UK"]["api"] = orig_api
check("unlisted fetcher keeps the prior-year check", has_prior_year(rs), rs)

# 7. rebuild path (AU from ABS, structured): a new quarter equal to last year's
au = copy.deepcopy(COMMITTED["AU"]["history"])
au_q = sorted((h for h in au if "-Q" in h["date"]), key=lambda h: h["date"])
y, q = au_q[-1]["date"].split("-Q")
new_q = f"{int(y) + (q == '4')}-Q{1 if q == '4' else int(q) + 1}"
prior_q = f"{int(new_q[:4]) - 1}-Q{new_q[-1]}"
prior_val = next(h["value"] for h in au_q if h["date"] == prior_q)
rebuilt = [{"date": h["date"], "value": h["value"]} for h in au_q]
rebuilt.append({"date": new_q, "value": prior_val})
f.ANOMALY_LOG.clear()
f.merge_country_data(copy.deepcopy(COMMITTED), {
    "history": rebuilt, "latest": COMMITTED["AU"]["latest"], "fetched_from": "ABS",
    "history_replace": True, "history_source": "ABS"}, "AU")
rs = [r for a in f.ANOMALY_LOG for r in a["reasons"] if a["date"] == new_q]
check("AU rebuild: new quarter equal to prior year isn't a prior-year anomaly",
      not has_prior_year(rs), rs)
f.ANOMALY_LOG.clear()

print()
if FAILURES:
    print(f"{len(FAILURES)} failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("All anomaly-scope checks passed.")
