#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Offline tests for the scraper's "recent draft" guard (#127).

The guard used the draft file's mtime. actions/checkout sets mtime to the
checkout time, so on every runner the committed 2026-10-29 draft looked 0.0h
old and every scheduled auto-scrape run exited before scraping. The age now
comes from the draft's own _metadata.generated stamp.

Run: python3 scripts/test_cb_draft_age.py
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import auto_scrape_cb_forecasts as s  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def write(tmp, body):
    path = os.path.join(tmp, "draft.json")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body if isinstance(body, str) else json.dumps(body))
    return path


now = datetime(2026, 11, 26, 10, 11)
with tempfile.TemporaryDirectory() as tmp:
    # The real case: committed draft from Oct 29, file freshly checked out.
    p = write(tmp, {"_metadata": {"generated": "2026-10-29T10:13:35.703477"}})
    os.utime(p, None)  # mtime = now, like actions/checkout
    age = s.draft_age_hours(p, now)
    check("old draft with fresh mtime counts as old", age is not None and age > 24 * 27, age)

    p = write(tmp, {"_metadata": {"generated": (now - timedelta(hours=3)).isoformat()}})
    age = s.draft_age_hours(p, now)
    check("draft generated 3h ago still blocks", age is not None and age < 12, age)

    p = write(tmp, {"_metadata": {"generated": "2026-11-26T07:11:00+00:00"}})
    age = s.draft_age_hours(p)
    check("timezone-aware stamp is handled", age is not None, age)

    for label, body in [("no _metadata", {"forecasts": []}),
                        ("bad stamp", {"_metadata": {"generated": "yesterday"}}),
                        ("not JSON", "{oops"),
                        ("not an object", "[]")]:
        p = write(tmp, body)
        check(f"{label}: doesn't hold up the scrape", s.draft_age_hours(p, now) is None)

    check("missing file: doesn't hold up the scrape",
          s.draft_age_hours(os.path.join(tmp, "nope.json"), now) is None)

# The committed draft in the repo must not block a run today.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
age = s.draft_age_hours(os.path.join(REPO, "docs/data/cb_forecasts_draft.json"), now)
check("committed draft doesn't block a scheduled run", age is None or age >= 12, age)

print()
if FAILURES:
    print(f"{len(FAILURES)} failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("All draft-age checks passed.")
