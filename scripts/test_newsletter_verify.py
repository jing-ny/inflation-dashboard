#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regression tests for the newsletter draft verifier (#117).

Both cases below are real drafts this pipeline produced and a human caught by
reading them. They are the reason verify_draft exists, so they are pinned here:

  2026-08-22  "China's July CPI sat at 0.5%, unchanged" — CN had just moved
              1.0 -> 0.5, the largest change in the data. The old snapshot diff
              compared against a snapshot that already carried 0.5.
  2026-08-23  "Korea ... up from 2.2% in March — a 0.59pp gain and the only
              change this period clearing the materiality threshold." The 0.59pp
              was the KR source migration (#58) backfilling 30 months, not an
              inflation move. July was actually DOWN 0.37pp from June.

Self-contained: no network, no API key, no git history. To replay the full
original drafts against the data they were generated from:

    git show 04c9875:docs/drafts/newsletter_2026-08-22.md
    git show 8dae064:docs/drafts/newsletter_2026-08-23.md

Run: python3 scripts/test_newsletter_verify.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_newsletter import (
    _figures, check_no_change_claims, compare_periods, source_blob, verify_draft,
)


def blocking(draft, source, changes):
    """Only the blocking half — advisory warnings never stop the job."""
    return verify_draft(draft, source, changes)[0]


def advisory(draft, source, changes):
    return verify_draft(draft, source, changes)[1]

FAILURES = []


def check(name: str, condition: bool, detail: str = ""):
    print(f"  {'PASS' if condition else 'FAIL'}  {name}")
    if not condition:
        FAILURES.append(f"{name}{': ' + detail if detail else ''}")


def fixture():
    """Minimal dataset in the shape of historical_cpi.json."""
    data = {
        "metadata": {"last_updated": "2026-08-23"},
        "CN": {
            "name": "China", "frequency": "monthly",
            "latest": {"date": "2026-07", "value": 0.5},
            "previous": {"date": "2026-06", "value": 1.0},
            "history": [{"date": "2026-05", "value": 1.2},
                        {"date": "2026-06", "value": 1.0},
                        {"date": "2026-07", "value": 0.5}],
        },
        "KR": {
            "name": "South Korea", "frequency": "monthly",
            "latest": {"date": "2026-07", "value": 2.79},
            "previous": {"date": "2026-06", "value": 3.16},
            "history": [{"date": "2026-05", "value": 3.14},
                        {"date": "2026-06", "value": 3.16},
                        {"date": "2026-07", "value": 2.79}],
        },
        "US": {
            "name": "United States", "frequency": "monthly",
            "latest": {"date": "2026-07", "value": 3.36},
            "previous": {"date": "2026-06", "value": 3.53},
            "history": [{"date": "2026-05", "value": 3.4},
                        {"date": "2026-06", "value": 3.53},
                        {"date": "2026-07", "value": 3.36}],
        },
    }
    changes = compare_periods(data)
    cb = {"forecasts": {
        # CN carries a policy rate because a test sentence quotes it: "the 1Y
        # LPR unchanged at 3.00%" must reach check_no_change_claims, not be
        # rejected by the figure rule for an unsourced 3.00.
        "CN": {"source": "IMF", "publication_date": "April 2026",
               "projections": {"2026": 1.2}, "policy_rate": {"rate": "3.00%"},
               "note": "PBoC publishes no standardized forecast."},
        "UK": {
        "source": "BoE", "publication_date": "April 2026",
        "projections": {"2026": 3.35}, "policy_rate": {"rate": "3.75%"},
        # En-dash on purpose: escaped as – this used to be read as the
        # number 20133.6, losing 3.6 and flagging a sourced figure as invented.
        "note": "CPI inflation spans 3.1–3.6% in 2026 across scenarios.",
    }}}
    imf = {"version": "April 2026", "retrieved": "2026-08-17",
           "note": "Broad upside revisions (US +0.8pp, AU/NZ +1.0pp).",
           "countries": {"CN": {"name": "China", "forecasts": {"2026": 1.2}}}}
    return changes, source_blob(changes, cb, imf)


def main() -> int:
    changes, source = fixture()
    by_code = {c.code: c for c in changes}

    print("\ncompare_periods — adjacent reference periods, not snapshots")
    check("CN reports the real -0.50pp move",
          by_code["CN"].delta_pp == -0.5 and by_code["CN"].is_material,
          f"got {by_code['CN'].delta_pp}")
    check("KR falls 0.37pp rather than rising 0.59pp",
          by_code["KR"].delta_pp == -0.37, f"got {by_code['KR'].delta_pp}")
    check("KR compares 2026-06 -> 2026-07",
          (by_code["KR"].previous_period, by_code["KR"].current_period) == ("2026-06", "2026-07"))

    print("\nverify_draft — the two drafts that shipped wrong")
    check("2026-08-22: 'unchanged' on a country that moved is caught (advisory)",
          bool(advisory("China's July CPI sat at 0.5%, unchanged, against "
                        "an IMF 2026 forecast of 1.2%.", source, changes)))
    check("2026-08-23: a delta from a period we never supplied is caught",
          bool(blocking("Korea rose to 2.79% in July, up from 2.2% in "
                            "March — a 0.59pp gain.", source, changes)))

    print("\nverify_draft — must stay quiet on correct copy")
    check("real delta passes",
          not blocking("US CPI eased to 3.36% in July from 3.53% "
                           "(-0.17pp).", source, changes))
    check("'unchanged' about a different number nearby passes",
          not blocking("China was 0.5% in July, with the 1Y LPR unchanged "
                           "at 3.00% for ten months.", source, changes))
    check("pp figure sourced from the IMF note passes",
          not blocking("The WEO revised the US up 0.8pp.", source, changes))
    check("BoE scenario figure behind an en-dash passes",
          not blocking("BoE scenarios span 3.1-3.6% this year.", source, changes))
    check("correct description of KR passes",
          not blocking("Korea eased to 2.79% in July, down 0.37pp from "
                           "June's 3.16%.", source, changes))

    print("\nverify_draft — counterexamples from the Codex review of #122")
    check("sign disagreement: 'rose 0.50pp' when CN fell 0.50pp (advisory)",
          bool(advisory("China CPI rose 0.50pp in July.", source, changes)))
    check("a CPI level does not license a delta of the same size (3.1pp)",
          bool(blocking("China CPI rose 3.1pp in July.", source, changes)))
    check("'held at' is caught like 'unchanged' (advisory)",
          bool(advisory("China CPI held at 0.5% in July.", source, changes)))
    check("adjectival country name is caught (advisory)",
          bool(advisory("Chinese CPI was 0.5%, unchanged.", source, changes)))
    check("no-change word BEFORE the figure is caught (advisory)",
          bool(advisory("US CPI was unchanged at 3.36%.", source, changes)))
    check("a self-computed pp gap is rejected (source forbids it)",
          bool(blocking("The BoE sees 3.35% against the IMF, a 0.15pp gap.",
                            source, changes)))
    check("negative percent is read as negative, not positive",
          _figures("Growth was -0.6%.", "%") == [-0.6],
          f"got {_figures('Growth was -0.6%.', '%')}")
    check("thousands separator is not silently truncated to 000pp",
          _figures("A 1,000pp move.", "pp") == [],
          f"got {_figures('A 1,000pp move.', 'pp')}")
    check("'percentage points' spelled out is checked too",
          bool(blocking("China rose 3.1 percentage points.", source, changes)))
    check("uppercase PP is checked too",
          bool(blocking("China rose 3.1PP.", source, changes)))

    print("\nverify_draft — false positives found while fixing the review findings")
    # The real regression: ZA's 5.0 headline matched the tail of "2.5%" in a
    # sentence about the BOK. Tested on the check itself so the figure rule
    # (which would reject an unsourced 10.5%) does not mask the result.
    check("a country's figure does not match inside a longer number",
          not check_no_change_claims("Policy rates sit at 10.5%, unchanged.", changes),
          str(check_no_change_claims("Policy rates sit at 10.5%, unchanged.", changes)))
    check("proximity window does not cross a sentence boundary",
          not blocking("China printed 0.5% in July. Steady policy followed.",
                           source, changes))
    check("'down 0.37pp' is not read as an increase for lacking a + sign",
          not blocking("Korea, down 0.37pp on the month.", source, changes))
    check("an explicit wrong sign is still caught",
          bool(blocking("Korea moved +0.37pp on the month.", source, changes)))

    check("prompt instruction text cannot license a figure",
          bool(blocking("The RBA's 3.3% is 0.7pp above the IMF's 4.0%.", source, changes)))
    check("thousands separator is rejected, not skipped",
          bool(blocking("China CPI jumped 1,000pp.", source, changes)))
    check("a supplied +0.8pp does not license a written -0.8pp",
          bool(blocking("The WEO revised the US -0.8pp.", source, changes)))

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILED:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("All newsletter verifier checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
