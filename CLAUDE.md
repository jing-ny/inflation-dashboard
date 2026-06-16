# CLAUDE.md

Project-specific guidance for Claude Code (and humans) working on `inflation-dashboard`.

## Principles

### 1. No manual data entry as a fallback

When a data source breaks (scraper 404, WAF block, restructured HTML, PDF table that won't extract cleanly), **do not** propose "mark this source as manual-entry" as a solution — even if the publication is infrequent (e.g. quarterly).

This dashboard is automation-first. The maintenance cost of remembering to manually update a JSON every quarter compounds with every source we add, and the "set it and forget it" model breaks the moment we accept hand-edited data alongside scraped data.

When automation is hard, the options are:

1. **Fix it properly** — new URL pattern, new dependency (`curl_cffi`, `pdfplumber`, headless browser), new extractor.
2. **Defer it** — leave the issue open, accept that the source goes stale until someone has time to do option 1.

That's it. "Just enter it by hand" is not on the menu.

### 2. Every number is validated, or labeled as not yet validated

Every numeric value displayed by the dashboard must either:

- have passed the project's validation (anomaly detector, range checks, source consistency check), **or**
- carry an explicit unvalidated flag in the data record (e.g. `"validated": false` or `"status": "draft"`) and be presented to readers as such.

Unmarked numbers are presumed validated. Don't add a number without making this state explicit, and don't silently pass an unvalidated number through to the public dashboard.

### 3. Every record carries provenance

For any data point we publish — historical CPI, central-bank forecast, IMF projection — the underlying record must include:

- `source_url`: the canonical page or PDF the value was pulled from
- `fetch_date` (for scraped data) or `source_date` (for forecasts): when we got it / what publication it's from

If a number can't be traced back to an original source via fields on the record itself, it doesn't belong in the dataset. "The link is documented in the README" is not enough — provenance lives on the record.

### 4. Stale data must be visibly stale

If a source breaks, the dashboard should communicate that the value is out of date — not silently keep showing the last successful fetch as if it were current. A frozen number with no staleness indicator misleads readers and makes "no manual entry" (#1) materially worse, because broken sources stop being noticed.

Acceptable patterns: a "last updated" badge per country/source, a visual greying/strikethrough when the gap exceeds the publication cadence, or omitting the country entirely. Whatever the mechanism, "no signal" is not a valid state for a broken source.

### 5. Trust the anomaly detector — don't silence the alarm

When `STEP_THRESHOLD_PP` (or any future check) fires, treat it as a signal that something's wrong with the source data, the scraper, or the comparison logic — **not** as a CI annoyance to be raised, looser-ed, or `|| true`'d away.

If anomalies fire on real data, the fix is to investigate *why* — fetcher bug, scraper miscapture, source revision, threshold being applied to the wrong neighbor — and address the cause. Bumping the threshold or adding broad exemptions is a strict last resort, and never the first move.

### 6. Every change goes through an issue and a PR — never merge without review

For any change to this repo, the workflow is: **open a GitHub issue** describing the problem/intent, then **open a pull request** (on a branch, never committing straight to `main`) that references it, and **wait for the maintainer's explicit review and approval before merging**.

Do not commit directly to `main`, do not self-merge, and do not merge a PR on the maintainer's behalf — even for a one-line fix, a "trivial" cleanup, or something that looks obviously correct. The issue gives the change a paper trail; the PR gives the maintainer a reviewable diff and the chance to say no. "It's small" is not an exception.

Claude may create the issue, the branch, and the PR, and may push follow-up commits to that PR's branch in response to review — but the **merge** is the maintainer's action, not Claude's.
