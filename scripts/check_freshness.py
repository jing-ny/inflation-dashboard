#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Freshness gate for the published CPI dataset.
=============================================

`monitor_updates.py` already *detects* stale series and emails about them, but
it exits 0 and its workflow step carries `continue-on-error: true`, so a source
that has been dead for years still produces a green run. KR sat at 172 days old
and IN at 141 for months with nothing going red (#116; the dead sources
themselves are #58 and #118).

This script gives that signal teeth. It is deliberately dumb and offline: it
reads the committed dataset and fails the build if any series is in the RED
staleness tier. No network, no API key — staleness is a property of the data we
publish, so the gate can run as the last step of any workflow that touches it.

Thresholds are imported from monitor_updates so the gate, the email monitor and
the front-end pills (docs/freshness.js) cannot drift apart — CLAUDE.md #4:
"no signal" is not a valid state for a broken source.

Usage:
    python scripts/check_freshness.py            # exit 1 if anything is red
    python scripts/check_freshness.py --warn-only  # always exit 0 (reporting)
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monitor_updates import CPI_STALE_THRESHOLDS
from fetch_historical_cpi import DISPLAY_ORDER

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "docs", "data", "historical_cpi.json")


def parse_reference_date(s: str) -> datetime:
    """Parse a stored latest.date into a datetime anchored at the reference period.

    Mirrors monitor_updates.check_cpi_freshness — monthly (2026-07), quarterly
    (2026-Q2, anchored to the last month of the quarter) or full (2026-07-15).
    Raises ValueError on anything else; the caller turns that into a failure
    rather than skipping, because an unparseable date is also "no signal".
    """
    if "-Q" in s:
        year, quarter = s.split("-Q")
        return datetime(int(year), int(quarter) * 3, 1)
    if len(s) == 10:
        return datetime.strptime(s, "%Y-%m-%d")
    return datetime.strptime(s, "%Y-%m")


def evaluate(data: dict, today: datetime = None) -> list:
    """Return one row per country: (code, date, days_old, cadence, tier)."""
    today = today or datetime.now()
    countries = data.get("countries", data)
    rows = []

    # DISPLAY_ORDER, not the data file's keys: it is the list of what the
    # dashboard actually publishes, so dropping a country (India, #118) also
    # drops it from the gate, and a country that vanishes from the data file
    # entirely still gets caught below rather than silently disappearing.
    for code in DISPLAY_ORDER:
        record = countries.get(code)
        if not isinstance(record, dict):
            rows.append((code, None, None, None, "RED"))
            continue
        latest = (record.get("latest") or {}).get("date")
        if not latest:
            rows.append((code, None, None, None, "RED"))
            continue

        try:
            ref = parse_reference_date(latest)
        except (ValueError, TypeError):
            rows.append((code, latest, None, None, "RED"))
            continue

        cadence = "quarterly" if (
            (record.get("frequency") or "").lower() == "quarterly"
            or (not record.get("frequency") and "-Q" in latest)
        ) else "monthly"
        green_max, amber_max = CPI_STALE_THRESHOLDS[cadence]

        days_old = max(0, (today - ref).days)
        if days_old > amber_max:
            tier = "RED"
        elif days_old > green_max:
            tier = "AMBER"
        else:
            tier = "GREEN"
        rows.append((code, latest, days_old, cadence, tier))

    return sorted(rows, key=lambda r: (-(r[2] or 10**6), r[0]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail the build on red-tier stale CPI series")
    parser.add_argument("--warn-only", action="store_true",
                        help="report but always exit 0")
    args = parser.parse_args()

    with open(DATA_PATH) as f:
        data = json.load(f)

    rows = evaluate(data)
    red = [r for r in rows if r[4] == "RED"]

    icon = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}
    lines = ["| Country | Latest | Age | Cadence | Tier |", "|---|---|---|---|---|"]
    print(f"{'code':<6}{'latest':<10}{'age':>6}  cadence     tier")
    for code, latest, days, cadence, tier in rows:
        age = f"{days}d" if days is not None else "—"
        print(f"{code:<6}{latest or '—':<10}{age:>6}  {cadence or '—':<11} {icon[tier]} {tier}")
        lines.append(f"| {code} | {latest or '—'} | {age} | {cadence or '—'} | {icon[tier]} {tier} |")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write("## CPI freshness gate\n\n" + "\n".join(lines) + "\n")

    if not red:
        print("\n✅ No series in the red staleness tier.")
        return 0

    detail = ", ".join(f"{c} ({d or '?'} @ {l or 'no date'})" for c, l, d, _, _ in red)
    print(f"\n🔴 {len(red)} series past the red threshold: {detail}")
    if args.warn_only:
        print("--warn-only set; not failing the build.")
        return 0
    print("Fix the source, or drop the country from the dashboard until it is "
          "fixed (CLAUDE.md #1/#4). Do not widen the threshold to make this pass.")
    return 1


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main())
